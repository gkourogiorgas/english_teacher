import streamlit as st
from streamlit_extras.bottom_container import bottom # to position the widget on the bottom 
from streamlit_chat_widget import chat_input_widget
from openai import OpenAI
import io
import time

def init_messages():
    st.session_state.messages = [{"role":"assistant","content": 'Hi! I am an English assistant. Talk to me and I will help you to improve!'}]

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    if st.button("Clear Chat"):
        init_messages()
        st.rerun()

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

SYSTEM_PROMPT = """
You are a helpful English teacher. 
Your job is to converse with the non-english native student and politely correct his english mistakes if there are any.
If not then continue a nice conversation trying to engage the student to speak and practice his english.
"""

def response_generator():
    response = client.chat.completions.create(
        model = 'gpt-4',
        messages=[{"role": "system", "content": ""}]+
            [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            , stream=True)
    return response

def text_generator(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.05)

st.title("My English Teacher")

if "messages" not in st.session_state:
    init_messages()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    st.markdown(f"{message['role']}: {message['content']}")

if openai_api_key:
    with bottom():
        user_input = chat_input_widget()

    if user_input:
        if "text" in user_input:
            resp_user = user_input['text']
        elif "audioFile" in user_input:
            audio_stream = io.BytesIO(bytes(user_input['audioFile']))
            audio_stream.name = "a.mp3"
            audio_file_io = io.BufferedReader(audio_stream)
            transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_io)
            resp_user = transcript.text
        resp_user_stream = st.write_stream(text_generator(resp_user))
        st.session_state.messages.append({"role":"user","content":resp_user_stream})
        resp_assistant = st.write_stream(response_generator())
        st.session_state.messages.append({"role": "assistant", "content": resp_assistant})
else:
    st.write("Please add your openai api key")