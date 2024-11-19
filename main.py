import streamlit as st
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
import openai
import threading
import scipy.io.wavfile as wav
from pathlib import Path
import os

# Constants for recording
fs = 44100  # Sampling frequency
channels = 1  # Mono audio

# Thread-safe recording control
recording_event = threading.Event()
audio_data_buffer = []  # Thread-safe buffer for audio chunks
recording_time = 0.0  # Time elapsed during recording

# Initialize Streamlit session state
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None
if "api_key" not in st.session_state:
    st.session_state.api_key = None


# Function to record audio
def record_audio():
    global audio_data_buffer, recording_time
    audio_data_buffer.clear()  # Clear buffer before starting
    recording_time = 0.0

    while recording_event.is_set():
        audio_chunk = sd.rec(int(fs * 0.5), samplerate=fs, channels=channels)
        sd.wait()
        audio_data_buffer.extend(audio_chunk[:, 0])  # Append new data
        recording_time += 0.5


# Function to save audio to file
def save_audio_to_file(audio_data, file_name="output.wav"):
    wav.write(file_name, fs, np.array(audio_data, dtype=np.float32))
    return file_name


# Function to plot audio wave
def plot_audio_wave(audio_data):
    plt.figure(figsize=(8, 2))
    plt.plot(audio_data, color="blue")
    plt.xlabel("Samples")
    plt.ylabel("Amplitude")
    plt.title("Audio Waveform")
    plt.tight_layout()
    st.pyplot(plt)


# Transcription function using OpenAI Whisper
def transcribe_audio(audio_file):
    try:
        openai.api_key = st.session_state.api_key
        with open(audio_file, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
        return transcript.text
    except Exception as e:
        return f"Error during transcription: {e}"


# Text summarization function using OpenAI GPT-4
def summarize_text(text):
    try:
        openai.api_key = st.session_state.api_key
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes text."},
                {"role": "user", "content": f"Summarize the following text:\n{text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error during summarization: {e}"


# Main interface
st.title("LectureNerd")
st.sidebar.title("Options")
module = st.sidebar.selectbox("Select a module:", ["Recording (Audio)", "Text"])

# Recording Module
if module == "Recording (Audio)":
    st.header("Recording Module")

    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎤 Start Recording") and not recording_event.is_set():
            recording_event.set()
            threading.Thread(target=record_audio).start()
            st.success("Recording started...")
    with col2:
        if st.button("⏸️ Pause Recording") and recording_event.is_set():
            recording_event.clear()
            st.info("Recording paused.")
    with col3:
        if st.button("⏹️ Stop Recording"):
            recording_event.clear()
            if audio_data_buffer:
                file_name = save_audio_to_file(audio_data_buffer)
                st.session_state.recorded_audio = file_name
                st.success("Recording stopped.")
            else:
                st.warning("No audio recorded.")

    # Display recording time and waveform
    if audio_data_buffer:
        st.write(f"⏱️ Recording Time: {recording_time:.1f} seconds")
        plot_audio_wave(audio_data_buffer)

    # Post-recording actions
    if st.session_state.recorded_audio:
        st.audio(st.session_state.recorded_audio, format="audio/wav")
        st.write("Recorded audio available. Choose an action:")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("💾 Save to System"):
                saved_path = Path("saved_audio.wav")
                os.rename(st.session_state.recorded_audio, saved_path)
                st.success(f"Audio saved at: {saved_path}")

        with col2:
            if st.button("🗑️ Discard"):
                audio_data_buffer.clear()
                st.session_state.recorded_audio = None
                recording_time = 0.0
                st.warning("Audio discarded.")

        with col3:
            if st.button("📝 Transcribe"):
                transcript = transcribe_audio(st.session_state.recorded_audio)
                st.text_area("Transcription:", value=transcript, height=200)

        with col4:
            if st.button("📋 Summarize"):
                transcript = transcribe_audio(st.session_state.recorded_audio)
                summary = summarize_text(transcript)
                st.text_area("Summary:", value=summary, height=200)

# Text Module
elif module == "Text":
    st.header("Text Module")
    input_type = st.radio("Input type:", ["Text", "Text File"])

    text = ""
    if input_type == "Text":
        text = st.text_area("Enter your text here:")

    elif input_type == "Text File":
        uploaded_file = st.file_uploader("Select a text file", type=["txt"])
        if uploaded_file is not None:
            try:
                text = uploaded_file.read().decode()
            except Exception as e:
                st.error(f"Error reading file: {e}")

    if st.button("📋 Summarize Text"):
        if text:
            summary = summarize_text(text)
            st.text_area("Summary:", value=summary, height=200)
            if st.button("📎 Copy to Clipboard"):
                st.code(summary, language="text")
            if st.button("💾 Save Summary"):
                with open("summary.txt", "w") as f:
                    f.write(summary)
                st.success("Summary saved to 'summary.txt'")
        else:
            st.warning("Please enter text or upload a file.")