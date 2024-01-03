import sounddevice as sd
import soundfile as sf
import numpy as np
from kivy.app import App
from kivy.uix.button import Button
from kivy.core.window import Window
import tempfile

import sounddevice as sd
import numpy as np
import os
import queue
import openai
from scipy.io.wavfile import write
from dotenv import load_dotenv
from openai import OpenAI

# Load the variables from .env file
load_dotenv()

# Retrieve and set the API key
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key is None:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY in the .env file.")
openai.api_key = openai_api_key

class AudioCapture(App):

    def build(self):
        self.record = False
        self.button = Button(text='Click or Press Space to Record')
        Window.bind(on_key_down=self.on_key_down)
        self.samplerate = 44100  # Sample rate
        self.duration = 10  # Max recording duration in seconds
        return self.button

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if text == ' ':
            self.toggle_recording()

    def toggle_recording(self):
        if not self.record:
            # Start recording
            self.record = True
            self.button.text = 'Recording... Press Space to Stop'
            self.start_recording()
        else:
            # Stop recording
            self.record = False
            self.button.text = 'Recording Stopped. Press Space to Start'
            self.stop_recording()

    def start_recording(self):
        self.recorded_data = []
        self.stream = sd.InputStream(callback=self.audio_callback, samplerate=self.samplerate, channels=1)
        self.stream.start()

    def stop_recording(self):
        self.stream.stop()
        self.stream.close()

        # Concatenate the recorded data along the first axis
        recorded_array = np.concatenate(self.recorded_data, axis=0)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        sf.write(temp_file.name, recorded_array, self.samplerate)
        print(f"Recording saved to {temp_file.name}")
        transcript = self.transcribe_audio(temp_file.name)
        print(transcript)


    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recorded_data.append(indata.copy())

    # Synchronous function to transcribe audio
    def transcribe_audio(self, file_path):
        """
        Transcribe the given audio file using OpenAI's Whisper API.

        Parameters:
        file_path (str): The path to the audio file to be transcribed.

        Returns:
        str: The transcribed text.
        """
        try:
            client = OpenAI()

            audio_file= open(file_path, "rb")
            transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="text"
            )
            return transcript

        except Exception as e:
            return f"An error occurred: {e}"

# if __name__ == '__main__':
#     MyAudioApp().run()
