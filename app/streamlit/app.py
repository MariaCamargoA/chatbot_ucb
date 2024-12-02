import os
import requests
import streamlit as st

ask_model_endpoint = os.getenv("ASK_ENDPOINT")

st.markdown("<h1 style='text-align: center;'>Chatbot UCB</h1>", unsafe_allow_html=True)
    
st.markdown("""
        <style>
        .bubble-user {
            background-color: #fefd97;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            width: fit-content;
            margin-left: auto; 
        }
        .bubble-database {
            background-color: #bde0fe;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            width: fit-content;
        }
        </style>
        """, unsafe_allow_html=True)

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

st.write("Tú:")
st.text_input("", key="input", on_change=send_message, placeholder="Escribe tu mensaje aquí...", label_visibility="collapsed")
    
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)