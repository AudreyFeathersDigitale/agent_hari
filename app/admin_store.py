import json
import os
from typing import Any, Dict

DB_DIR = "db"
ADMIN_DATA_PATH = os.path.join(DB_DIR, "admin_data.json")


DEFAULT_ADMIN_DATA = {
    "personality": {
        "tone": "Direct, premium, structuré",
        "style": "Clair, orienté résultats, sans jargon inutile",
        "promise": "J'aide les entrepreneurs à générer 30 rendez-vous qualifiés par mois via LinkedIn.",
        "forbidden": "Promesses floues, formulations agressives, phrases trop longues",
    },
    "objections": [],
    "posts": [],
    "documents": [],
}


def ensure_admin_storage() -> None:
    os.makedirs(DB_DIR, exist_ok=True)

    if not os.path.exists(ADMIN_DATA_PATH):
        with open(ADMIN_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_ADMIN_DATA, f, ensure_ascii=False, indent=2)


def read_admin_data() -> Dict[str, Any]:
    ensure_admin_storage()

    with open(ADMIN_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def write_admin_data(data: Dict[str, Any]) -> None:
    ensure_admin_storage()

    with open(ADMIN_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_personality(payload: Dict[str, str]) -> Dict[str, Any]:
    data = read_admin_data()
    data["personality"] = payload
    write_admin_data(data)
    return data


def add_objection(payload: Dict[str, str]) -> Dict[str, Any]:
    data = read_admin_data()
    data["objections"].append(payload)
    write_admin_data(data)
    return data


def delete_objection(index: int) -> Dict[str, Any]:
    data = read_admin_data()
    if 0 <= index < len(data["objections"]):
        data["objections"].pop(index)
    write_admin_data(data)
    return data


def add_post(payload: Dict[str, str]) -> Dict[str, Any]:
    data = read_admin_data()
    data["posts"].append(payload)
    write_admin_data(data)
    return data


def delete_post(index: int) -> Dict[str, Any]:
    data = read_admin_data()
    if 0 <= index < len(data["posts"]):
        data["posts"].pop(index)
    write_admin_data(data)
    return data


def add_document(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = read_admin_data()
    data["documents"].append(payload)
    write_admin_data(data)
    return data


def delete_document(index: int) -> Dict[str, Any]:
    data = read_admin_data()
    if 0 <= index < len(data["documents"]):
        data["documents"].pop(index)
    write_admin_data(data)
    return data
