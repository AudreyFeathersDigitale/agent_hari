import os
import shutil

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

from app.admin_store import (
    add_document,
    add_objection,
    add_post,
    delete_document,
    delete_objection,
    delete_post,
    ensure_admin_storage,
    read_admin_data,
    update_personality,
)
from app.memory import init_memory_db, add_message, get_history, clear_history

UPLOADS_DIR = "uploads"

app = FastAPI(
    title="Hari Backend",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
    "https://agent-hari-ui.vercel.app",]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_id: str
    message: str


class PersonalityPayload(BaseModel):
    tone: str
    style: str
    promise: str
    forbidden: str


class ObjectionPayload(BaseModel):
    objection: str
    answer: str


class PostPayload(BaseModel):
    title: str
    content: str


@app.on_event("startup")
def startup_event():
    init_memory_db()
    ensure_admin_storage()
    os.makedirs(UPLOADS_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"status": "ok"}


def extract_pdf_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        pages_text = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        return "\n\n".join(pages_text).strip()
    except Exception:
        return ""


def get_relevant_document_snippets(user_message: str, limit: int = 2) -> str:
    data = read_admin_data()
    documents = data.get("documents", [])

    query_words = set(user_message.lower().split())
    scored = []

    for doc in documents:
        extracted_text = doc.get("extracted_text", "")
        if not extracted_text:
            continue

        haystack = extracted_text.lower()
        score = sum(1 for word in query_words if word in haystack)

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    top_docs = scored[:limit]

    snippets = []
    for _, doc in top_docs:
        text = doc.get("extracted_text", "")[:1500]
        snippets.append(f"[Document: {doc.get('name', 'sans_nom')}]\n{text}")

    return "\n\n".join(snippets)


# =========================
# CHAT + MEMORY
# =========================

@app.get("/memory/{user_id}")
def read_memory(user_id: str):
    history = get_history(user_id)
    return {"user_id": user_id, "history": history}


@app.delete("/memory/{user_id}")
def delete_memory(user_id: str):
    clear_history(user_id)
    return {"status": "deleted", "user_id": user_id}


@app.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    user_message = req.message.strip()

    add_message(user_id, "user", user_message)

    history = get_history(user_id, limit=10)

    admin_data = read_admin_data()
    personality = admin_data.get("personality", {})
    objections = admin_data.get("objections", [])
    posts = admin_data.get("posts", [])

    last_user_messages = [
        msg["content"]
        for msg in history
        if msg["role"] == "user"
    ][-3:]

    message_lower = user_message.lower()

    objection_match = None
    for item in objections:
        if item["objection"].lower() in message_lower:
            objection_match = item
            break

    document_context = get_relevant_document_snippets(user_message)

    if objection_match:
        answer = objection_match["answer"]

    elif document_context:
        answer = (
            f"{personality.get('tone', 'Direct')} : j’ai trouvé un contenu pertinent dans les documents ajoutés.\n\n"
            f"{document_context}\n\n"
            "À partir de ce document, je te conseille de clarifier le message principal, la promesse et l’action suivante."
        )

    elif "lead" in message_lower or "rdv" in message_lower or "rendez-vous" in message_lower:
        answer = (
            f"{personality.get('tone', 'Direct')} : pour obtenir plus de rendez-vous qualifiés, "
            "il faut un positionnement clair, une offre forte et une prospection LinkedIn structurée."
        )

    elif "offre" in message_lower:
        answer = (
            "Une offre irrésistible repose sur 3 éléments : un problème clair, "
            "une transformation précise et une promesse forte."
        )

    elif "positionnement" in message_lower:
        answer = (
            "Un bon positionnement doit dire qui tu aides, sur quel problème précis, "
            "et avec quelle promesse différenciante."
        )

    elif "linkedin" in message_lower:
        answer = (
            "Sur LinkedIn, ton système doit reposer sur 3 piliers : un profil qui convertit, "
            "un contenu qui crédibilise et une prospection structurée."
        )

    elif "rappelle" in message_lower or "résume" in message_lower:
        if last_user_messages:
            answer = "Voici ce que j’ai retenu : " + " | ".join(last_user_messages)
        else:
            answer = "Je n’ai pas encore assez d’historique pour faire un résumé."

    elif posts:
        answer = (
            "Je peux m’appuyer sur les contenus déjà ajoutés à Hari. "
            f"Par exemple, la promesse actuelle est : {personality.get('promise', '')}"
        )

    else:
        answer = (
            "Je peux t’aider à générer des rendez-vous qualifiés via LinkedIn. "
            "Dis-moi ce que tu veux optimiser en priorité."
        )

    add_message(user_id, "assistant", answer)

    return {
        "answer": answer,
        "history": get_history(user_id, limit=10),
    }


# =========================
# ADMIN
# =========================

@app.get("/admin/data")
def get_admin_data():
    return read_admin_data()


@app.post("/admin/personality")
def save_personality(payload: PersonalityPayload):
    data = update_personality(payload.model_dump())
    return {"status": "saved", "data": data}


@app.post("/admin/objections")
def save_objection(payload: ObjectionPayload):
    data = add_objection(payload.model_dump())
    return {"status": "saved", "data": data}


@app.delete("/admin/objections/{index}")
def remove_objection(index: int):
    data = delete_objection(index)
    return {"status": "deleted", "data": data}


@app.post("/admin/posts")
def save_post(payload: PostPayload):
    data = add_post(payload.model_dump())
    return {"status": "saved", "data": data}


@app.delete("/admin/posts/{index}")
def remove_post(index: int):
    data = delete_post(index)
    return {"status": "deleted", "data": data}


@app.post("/admin/upload-pdf")
def upload_pdf(file: UploadFile = File(...), category: str = Form("general")):
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    safe_name = file.filename
    file_path = os.path.join(UPLOADS_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    extracted_text = extract_pdf_text(file_path)

    document_payload = {
        "name": safe_name,
        "category": category,
        "path": file_path,
        "size": str(file_size),
        "extracted_text": extracted_text,
    }

    data = add_document(document_payload)

    return {
        "status": "uploaded",
        "file": {
            "name": safe_name,
            "category": category,
            "size": str(file_size),
            "text_extracted": bool(extracted_text),
        },
        "data": data,
    }


@app.delete("/admin/documents/{index}")
def remove_document(index: int):
    data_before = read_admin_data()
    documents = data_before.get("documents", [])

    if 0 <= index < len(documents):
        path = documents[index].get("path")
        if path and os.path.exists(path):
            os.remove(path)

    data = delete_document(index)
    return {"status": "deleted", "data": data}
