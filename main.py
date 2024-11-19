import tkinter as tk
from tkinter import ttk, filedialog
import openai
import threading

# Set your OpenAI API key
openai.api_key = "YOUR_API_KEY"

def transcribe_audio(audio_file):
  """Transcribes audio using OpenAI Whisper."""
  try:
    with open(audio_file, "rb") as f:
      transcript = openai.Audio.transcribe("whisper-1", f)
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
    text = text_input.get("1.0", tk.END).strip()
    if text:
      summary = summarize_text(text)
      result_label.config(text=summary)
    else:
      result_label.config(text="Please enter some text.")
  elif input_type == "audio":
    audio_file = audio_file_var.get()
    if audio_file:
      # Disable the button while processing
      process_button.config(state="disabled")
      result_label.config(text="Transcribing and summarizing...")

      # Transcribe in a separate thread to avoid freezing the UI
      def transcribe_and_summarize():
        transcript = transcribe_audio(audio_file)
        summary = summarize_text(transcript)
        result_label.config(text=summary)
        process_button.config(state="normal")

      threading.Thread(target=transcribe_and_summarize).start()
    else:
      result_label.config(text="Please select an audio file.")

def browse_audio_file():
  """Opens a file dialog to select an audio file."""
  filename = filedialog.askopenfilename(
    initialdir="/",
    title="Select an audio file",
    filetypes=(("Audio files", "*.mp3 *.wav *.m4a *.ogg"), ("all files", "*.*"))
  )
  audio_file_var.set(filename)

# Create the main window
root = tk.Tk()
root.title("Class Summarizer")

# Input type selection
input_var = tk.StringVar(value="text")
ttk.Radiobutton(root, text="Text", variable=input_var, value="text").grid(row=0, column=0, sticky="w")
ttk.Radiobutton(root, text="Audio", variable=input_var, value="audio").grid(row=1, column=0, sticky="w")

# Text input
text_input = tk.Text(root, wrap="word", height=10, width=50)
text_input.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Audio file selection
audio_file_var = tk.StringVar()
ttk.Entry(root, textvariable=audio_file_var, state="readonly", width=40).grid(row=3, column=0, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=browse_audio_file).grid(row=3, column=1, padx=10, pady=5, sticky="ew")

# Process button
process_button = ttk.Button(root, text="Summarize", command=process_input)
process_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Result label
result_label = ttk.Label(root, text="", wraplength=400)
result_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()