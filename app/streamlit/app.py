import os
import requests
import streamlit as st

ask_model_endpoint = os.getenv("ASK_ENDPOINT")
    
st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@700&family=Poppins:wght@400;700&display=swap');
        
        h1 {
            font-family: 'Roboto Slab', serif;
            font-size: 2.5em;
            color: black;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
        }
        .bubble-user {
            background-color: #fefd97;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            width: fit-content;
            margin-left: auto; 
            max-width: 100%;
        }
        .bubble-database {
            background-color: #bde0fe;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            max-width: 100%;
            width: fit-content;
        }
        </style>
        """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Chatbot UCB</h1>", unsafe_allow_html=True)

def set_input_text(message):
    st.session_state.input = message
    send_message()
        
if "history_chat_pdf" not in st.session_state:
        st.session_state.history_chat_pdf = []

if "input" not in st.session_state:
    st.session_state.input = ""

for chat in st.session_state.history_chat_pdf:
        st.markdown(f"<div class='bubble-user'>{chat['user']}</div>", unsafe_allow_html=True) 
        st.markdown(f"<div class='bubble-database'>{chat['response']}</div>", unsafe_allow_html=True)

def send_message():
    user_input = st.session_state.input
    if user_input:
        payload = {'query': user_input, 'model': "string"}
        try:
            response = requests.post(ask_model_endpoint, json=payload)
            if response.status_code == 200:
                data = response.json()
                output = data["response"]
                results = output
            else:
                results = f"Error: {response.text}"

        except Exception as e:
            results = f"Error: {str(e)}"

        st.session_state.history_chat_pdf.append({"user": user_input, "response": results})
        st.session_state.input = ""

common_messages = [
    "¿Qué es la beca cultural?",
    "¿Cómo postular a la beca comunidad?",
    "¿Cuántos tipos de becas ofrece la universidad?",
    "¿Cómo postular a la beca bachiller?",
    "¿Qué requisitos son necesarios para postular a la beca bachiller?",
    "¿Qué beneficios incluye la beca excelencia académica?",
    "¿Dónde puedo encontrar más información sobre las becas?",
    # "¿Hay becas específicas para estudiantes de bajos recursos?",
    "¿Puedo aplicar a una beca si soy estudiante extranjero?",
    "¿Qué tipos de becas deportivas están disponibles?",
    "¿Cómo se evalúan las solicitudes para otorgar una beca?",
]

st.sidebar.markdown("### Mensajes frecuentes")
for msg in common_messages:
    st.sidebar.button(msg, on_click=set_input_text, args=(msg,))

st.write("Tú:")
st.text_input("", key="input", on_change=send_message, placeholder="Escribe tu mensaje aquí...", label_visibility="collapsed")
    
st.markdown("</div>", unsafe_allow_html=True)