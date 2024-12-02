import streamlit as st
from streamlit_extras.bottom_container import (
    bottom,
)  # to position the widget on the bottom
from streamlit_mic_recorder import mic_recorder
from openai import OpenAI
import io
import time
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

DEEPGRAM_MODELS = [
    "nova-2",
    "nova-2-conversationalai",
    "nova-2-phonecall",
]
OPENAI_AUDIO_MODELS = ["whisper-1"]
OPENAI_LLMS = ["gpt-4", "chatgpt-4o-latest", "gpt-3.5-turbo-1106"]
red_square = "\U0001F7E5"
microphone = "\U0001F3A4"
play_button = "\U000025B6"


def init_messages():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I am an English assistant. Talk to me and I will help you to improve!",
        }
    ]


with st.sidebar:
    stt_model = st.selectbox("Select STT Model", OPENAI_AUDIO_MODELS + DEEPGRAM_MODELS)
    llm = st.selectbox("Select LLM", OPENAI_LLMS)
    if stt_model in OPENAI_AUDIO_MODELS or llm in OPENAI_LLMS:
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
    if stt_model in DEEPGRAM_MODELS:
        deepgram_api_key = st.text_input("Deepgram API Key", type="password")
        if deepgram_api_key:
            deepgram_client = DeepgramClient(deepgram_api_key)
    if st.button("Clear Chat"):
        init_messages()
        st.rerun()

SYSTEM_PROMPT = """
You are a helpful English teacher. 
Your job is to converse with the non-english native student and politely correct his english mistakes if there are any.
If not then continue a nice conversation trying to engage the student to speak and practice his english.
If you believe there is a better way for the student to say what he/she is trying to say, please provide the correct way.
Suggest more suitable vocabulary and phrases to the student if you think they are appropriate.
"""


def response_generator():
    response = openai_client.chat.completions.create(
        model=llm,
        messages=[{"role": "system", "content": ""}]
        + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )
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
                user_input_text = st.chat_input()
            with right:
                user_input_audio = mic_recorder(
                    key=None,
                    start_prompt=play_button + microphone,
                    stop_prompt=red_square,
                    just_once=True,
                    use_container_width=True,
                )
    if user_input_text or user_input_audio:
        if user_input_text:
            resp_user = user_input_text
        elif user_input_audio:
            audio_stream = io.BytesIO(user_input_audio["bytes"])
            audio_stream.name = "a.mp3"
            audio_file_io = io.BufferedReader(audio_stream)
            if stt_model in OPENAI_AUDIO_MODELS:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file_io
                )
                resp_user = transcript.text
            elif stt_model in DEEPGRAM_MODELS:
                payload: FileSource = {
                    "buffer": audio_file_io,
                }

                # STEP 2: Configure Deepgram options for audio analysis
                options = PrerecordedOptions(
                    model=stt_model,
                    smart_format=True,
                )

                # STEP 3: Call the transcribe_file method with the text payload and options
                response = deepgram_client.listen.rest.v("1").transcribe_file(
                    payload, options
                )

                # STEP 4: Print the response
                print(response.to_json(indent=4))
                resp_user = response["results"]["channels"][0]["alternatives"][0][
                    "transcript"
                ]
        with st.chat_message("user"):
            resp_user_stream = st.write_stream(text_generator(resp_user))
            st.session_state.messages.append(
                {"role": "user", "content": resp_user_stream}
            )
        with st.chat_message("assistant"):
            resp_assistant = st.write_stream(response_generator())
            st.session_state.messages.append(
                {"role": "assistant", "content": resp_assistant}
            )
else:
    st.write("Please add your openai api key")
