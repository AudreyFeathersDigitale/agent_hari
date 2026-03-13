import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Clone Expert", page_icon="🧠", layout="centered")

st.title("🧠 Clone Expert")
st.caption("Interface simple pour tester ton agent comme un mini ChatGPT")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Paramètres")
    user_id = st.text_input("Identifiant utilisateur", value="client_test")
    api_url = st.text_input("URL API", value=API_URL)
    if st.button("Vider la conversation"):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Écris ton message...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        response = requests.post(
            api_url,
            json={
                "user_id": user_id,
                "message": prompt,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer", "Aucune réponse renvoyée par l'API.")
    except requests.exceptions.RequestException as e:
        answer = f"Erreur de connexion à l'API : {e}"
    except ValueError:
        answer = "Erreur : la réponse de l'API n'est pas un JSON valide."

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.markdown(answer)