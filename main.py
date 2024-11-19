import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import openai
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os

# Set your OpenAI API key
openai.api_key = "YOUR_API_KEY"

# Audio recording parameters
fs = 44100  # Sample rate
channels = 1  # Mono recording

# Global variables for audio recording
recording = False
audio_data = []

def transcribe_audio(audio_data=None, audio_file=None):
  """Transcribes audio using OpenAI Whisper."""
  try:
    if audio_data is not None:
      # Save the recorded audio data to a temporary file
      temp_file = "temp_audio.wav"
      wav.write(temp_file, fs, np.array(audio_data, dtype=np.int16))
      with open(temp_file, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
      os.remove(temp_file)  # Remove the temporary file
    elif audio_file is not None:
      with open(audio_file, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    else:
      return "No audio data or file provided."
    return transcript.text
  except Exception as e:
    return f"Error transcribing audio: {e}"

def summarize_text(text):
  """Summarizes text using OpenAI GPT."""
  try:
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": "You are a helpful assistant that summarizes text."},
        {"role": "user", "content": f"Please summarize the following text:\n{text}"}
      ]
    )
    return response.choices[0].message.content.strip()
  except Exception as e:
    return f"Error summarizing text: {e}"

def process_input():
  """Processes text or audio input and displays the summary."""
  input_type = input_var.get()
  if input_type == "text":
    file_path = file_path_var.get()
    if file_path:
      try:
        if file_path.endswith(".txt"):
          with open(file_path, "r") as f:
            text = f.read()
        elif file_path.endswith(".pdf"):
          # You'll need to install a library like PyPDF2 to read PDFs
          # Example:
          # import PyPDF2
          # with open(file_path, "rb") as f:
          #   reader = PyPDF2.PdfReader(f)
          #   text = ""
          #   for page in reader.pages:
          #     text += page.extract_text()
          text = "PDF reading not implemented yet."  # Replace with actual PDF reading
        elif file_path.endswith((".doc", ".docx")):
          # You'll need to install a library like python-docx to read Word files
          # Example:
          # import docx
          # doc = docx.Document(file_path)
          # text = ""
          # for paragraph in doc.paragraphs:
          #   text += paragraph.text
          text = "Word document reading not implemented yet."  # Replace with actual Word reading
        else:
          result_label.config(text="Unsupported file type.")
          return

        summary = summarize_text(text)
        result_label.config(text=summary)
      except Exception as e:
        result_label.config(text=f"Error reading file: {e}")
    else:
      result_label.config(text="Please select a file.")
  elif input_type == "audio":
    global audio_data
    summary = summarize_text(transcribe_audio(audio_data=audio_data))
    result_label.config(text=summary)
    audio_data = []  # Clear recorded audio data

def browse_file():
  """Opens a file dialog to select a text file."""
  filename = filedialog.askopenfilename(
    initialdir="/",
    title="Select a file",
    filetypes=(("Text files", "*.txt"), ("PDF files", "*.pdf"), ("Word files", "*.doc *.docx"), ("all files", "*.*"))
  )
  file_path_var.set(filename)

def start_recording():
  """Starts audio recording."""
  global recording, audio_data
  recording = True
  audio_data = []
  record_button.config(text="Pause", command=pause_recording)
  stop_button.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

  def record_audio():
    global audio_data
    while recording:
      audio_chunk = sd.rec(int(fs * 0.5), samplerate=fs, channels=channels)  # Record in chunks
      sd.wait()  # Wait until recording is finished
      audio_data.extend(audio_chunk[:, 0])  # Append the chunk to the audio data

  threading.Thread(target=record_audio).start()

def pause_recording():
  """Pauses audio recording."""
  global recording
  recording = False
  record_button.config(text="Record", command=start_recording)

def stop_recording():
  """Stops audio recording and provides options."""
  global recording, audio_data
  recording = False
  record_button.config(text="Record", command=start_recording)
  stop_button.grid_forget()

  def save_audio(file_path):
    wav.write(file_path, fs, np.array(audio_data, dtype=np.int16))
    result_label.config(text=f"Audio saved to {file_path}")

  def transcribe_and_summarize():
    transcript = transcribe_audio(audio_data=audio_data)
    summary = summarize_text(transcript)
    result_label.config(text=summary)

  # Ask the user what to do with the recording
  result = messagebox.askquestion(
    "Recording stopped",
    "What do you want to do with the recording?",
    type="yesnocancel"
  )
  if result == "yes":  # Save
    save_file_path = filedialog.asksaveasfilename(
      defaultextension=".wav",
      filetypes=(("WAV files", "*.wav"), ("all files", "*.*"))
    )
    if save_file_path:
      save_audio(save_file_path)
      # Add option to save the path for future recordings here (not implemented)
  elif result == "no":  # Delete
    audio_data = []
    result_label.config(text="Recording deleted.")
  elif result == "cancel":  # Continue recording
    start_recording()
  else:
    pass  # Do nothing

def switch_input_type():
  """Switches between text and audio input UI."""
  input_type = input_var.get()
  if input_type == "text":
    # Show text input UI
    file_path_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    file_path_entry.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
    browse_button.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
    # Hide audio input UI
    record_button.grid_forget()
    stop_button.grid_forget()
  elif input_type == "audio":
    # Hide text input UI
    file_path_label.grid_forget()
    file_path_entry.grid_forget()
    browse_button.grid_forget()
    # Show audio input UI
    record_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Create the main window
root = tk.Tk()
root.title("Class Summarizer")

# Input type selection
input_var = tk.StringVar(value="text")
ttk.Radiobutton(root, text="Text", variable=input_var, value="text", command=switch_input_type).grid(row=0, column=0, sticky="w")
ttk.Radiobutton(root, text="Audio", variable=input_var, value="audio", command=switch_input_type).grid(row=1, column=0, sticky="w")

# Text input UI
file_path_var = tk.StringVar()
file_path_label = ttk.Label(root, text="Select a file:")
file_path_entry = ttk.Entry(root, textvariable=file_path_var, state="readonly", width=40)
browse_button = ttk.Button(root, text="Browse", command=browse_file)
# Initially show text input UI
file_path_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
file_path_entry.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
browse_button.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

# Audio input UI
record_button = ttk.Button(root, text="Record", command=start_recording)
stop_button = ttk.Button(root, text="Stop", command=stop_recording)

# Process button
process_button = ttk.Button(root, text="Summarize", command=process_input)
process_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Result label
result_label = ttk.Label(root, text="", wraplength=400)
result_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()