import streamlit as st
from streamlit_extras.bottom_container import bottom # to position the widget on the bottom 
from streamlit_mic_recorder import mic_recorder
from openai import OpenAI
import io
import time

red_square = "\U0001F7E5"
microphone = "\U0001F3A4"
play_button = "\U000025B6"

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

if openai_api_key:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    with bottom():
        with st.container():
            left, right = st.columns([0.9, 0.1])
            with left:
                user_input = st.chat_input()
            with right:
                user_input = mic_recorder(
            key=None,
            start_prompt=play_button + microphone,
            stop_prompt=red_square,
            just_once=True,
            use_container_width=True,
        )

    if user_input:
        if isinstance(user_input,str):
            resp_user = user_input
        else:
            audio_stream = io.BytesIO(user_input['bytes'])
            audio_stream.name = "a.mp3"
            audio_file_io = io.BufferedReader(audio_stream)
            transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_io)
            resp_user = transcript.text
        with st.chat_message("user"):
            resp_user_stream = st.write_stream(text_generator(resp_user))
            st.session_state.messages.append({"role":"user","content":resp_user_stream})
        with st.chat_message("assistant"):
            resp_assistant = st.write_stream(response_generator())
            st.session_state.messages.append({"role": "assistant", "content": resp_assistant})
else:
    st.write("Please add your openai api key")