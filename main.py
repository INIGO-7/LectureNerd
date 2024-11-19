import streamlit as st
import openai
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os

# Set your OpenAI API key
# openai.api_key = st.secrets["OPENAI_API_KEY"]  # Si usas secrets de Streamlit
openai.api_key = "YOUR_API_KEY"  # Reemplaza con tu clave API

# Audio recording parameters
fs = 44100
channels = 1

# Global variables
recording = False
audio_data = []


def transcribe_audio(audio_data=None, audio_file=None):
    """Transcribes audio using OpenAI Whisper."""
    try:
        if audio_data is not None:
            temp_file = "temp_audio.wav"
            wav.write(temp_file, fs, np.array(audio_data, dtype=np.int16))
            with open(temp_file, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
            os.remove(temp_file)
        elif audio_file is not None:
            with open(audio_file, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
        else:
            return "No audio data or file provided."
        return transcript.text
    except Exception as e:
        return f"Error transcribing audio: {e}"


def summarize_text(text):
    """Summarizes text using OpenAI GPT-4."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Please summarize the following text:\n{text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error summarizing text: {e}"


# Interfaz de Streamlit
st.title("Class Summarizer")

input_type = st.radio("Tipo de entrada:", ("Texto", "Audio"))

if input_type == "Texto":
    # Caja de texto para pegar texto
    pasted_text = st.text_area("Pega aquí tu texto:")

    # Subir archivo de texto
    uploaded_file = st.file_uploader("O bien, selecciona un archivo de texto",
                                     type=["txt", "pdf", "docx"])

    if uploaded_file is not None:
        try:
            text = uploaded_file.read().decode()
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
    else:
        text = pasted_text  # Usar el texto pegado si no se subió ningún archivo

    if st.button("Resumir"):
        if text:
            summary = summarize_text(text)
            st.text_area("Resumen:", value=summary, height=200)
        else:
            st.warning("Por favor, introduce texto o sube un archivo.")

elif input_type == "Audio":
    if st.button("Grabar"):
        recording = True
        audio_data = []
        st.write("Grabando...")

        def record_audio():
            global audio_data
            while recording:
                audio_chunk = sd.rec(int(fs * 0.5),
                                     samplerate=fs,
                                     channels=channels)
                sd.wait()
                audio_data.extend(audio_chunk[:, 0])

        threading.Thread(target=record_audio).start()

    if st.button("Detener"):
        recording = False
        st.write("Grabación detenida.")

    if st.button("Resumir"):
        if audio_data:
            transcript = transcribe_audio(audio_data=audio_data)
            summary = summarize_text(transcript)
            st.text_area("Resumen:", value=summary, height=200)
        else:
            st.warning("Primero debes grabar audio.")