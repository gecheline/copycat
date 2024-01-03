from kivymd.app import MDApp
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dropdownitem import MDDropDownItem
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.list import OneLineListItem
from kivy.core.window import Window


import tempfile

import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import openai
from scipy.io.wavfile import write
from dotenv import load_dotenv
from openai import OpenAI

import elevenlabs
from elevenlabs import Voice, VoiceSettings, generate, stream, set_api_key

# Load the variables from .env file
load_dotenv()

# Retrieve and set the API key
openai_api_key = os.getenv('OPENAI_API_KEY')
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
if openai_api_key is None:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY in the .env file.")
openai.api_key = openai_api_key
set_api_key(elevenlabs_api_key)

from talk2persona import PersonaAgent

# class ItemDropdown(OneLineListItem):
#     text = StringProperty()


class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)
        self.template_selected = False
        self.current_template = ""
        self.storyline_visible = False
        self.selected_button = None

    def show_template_and_inputs(self):
        self.template_selected = True
        self.update_text()
        self.ids.template_and_inputs_layout.opacity = 1
        self.ids.template_and_inputs_layout.disabled = False

    def set_fantasy_template(self):
        self.current_template = ('''Assume the persona of {0}, who lives in a fantasy world. You are special though. You {1}. One day, you {2} and all of a sudden {3}.You are feeling {4} and that is reflected in the tone you use in the responses, which is also {4}.
                                    ''')
        self.show_template_and_inputs()

    def set_mundane_template(self):
        self.current_template = ('''Assume the persona of {0}, who has been taken out of their world and now lives in the real world. In the real world, you {1}. One day, you {2} and all of a sudden {3}. You are feeling {4} and that is reflected in the tone you use in the responses, which is also {4}.
                                 ''')
        self.show_template_and_inputs()

    def update_text(self, *args):
        if self.template_selected:
            input_texts = [self.ids['input{}'.format(i)].text for i in range(1, 6)]
            self.ids.big_text.text = self.current_template.format(*input_texts)

    def toggle_storyline_visibility(self):
        self.storyline_visible = not self.storyline_visible
        self.ids.big_text.opacity = 1 if self.storyline_visible else 0
        self.ids.big_text.disabled = not self.storyline_visible

    def select_button(self, button):
        app = MDApp.get_running_app()
        if self.selected_button:
            self.selected_button.md_bg_color = app.theme_cls.bg_normal
        button.md_bg_color = app.theme_cls.primary_color
        button.md_text_color = app.theme_cls.bg_normal
        self.selected_button = button

    def temporary_color_change(self, button, is_press):
        app = MDApp.get_running_app()
        if is_press:
            button.md_bg_color = '#000000'
        else:
            button.md_bg_color = app.theme_cls.primary_color

class SecondScreen(Screen):

    def __init__(self, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        self.record = False
        self.samplerate = 44100
        self.recorded_data = []
        self.input_device_menu = None
        self.output_device_menu = None
        self.voice_menu = None

    #     self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
    #     self._keyboard.bind(on_key_down=self._on_keyboard_down)

    # def _keyboard_closed(self):
    #     self._keyboard.unbind(on_key_down=self._on_keyboard_down)
    #     self._keyboard = None

    # def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
    #     # Check if '/' key is pressed
    #     if text=='/':
    #         self.toggle_recording()
    #     return True  # Return True to accept the key. Otherwise, it will propagate to other keyboard listeners.


    def on_pre_enter(self):
        self.ids.recording_text.text = 'Press to Record'
        self.setup_device_menus()
        self.setup_voice_menu()

        storyline = MDApp.get_running_app().root.get_screen('first').ids.big_text.text
        # Assuming 'character' is another piece of information you have
        character = MDApp.get_running_app().root.get_screen('first').ids.input1.text # Replace with actual character info
        self.initialize_chat(storyline, character)
        self.selected_voice_id = 'D38z5RcWu1voky8WS1ja'

    def setup_device_menus(self):
        # List input and output devices
        input_devices = [{'viewclass': 'MDDropDownItem', 'text': f"{device['name']}", 'on_release': lambda x=device['name']: self.set_input_device(x)} for device in sd.query_devices() if device['max_input_channels'] > 0]
        output_devices = [{'viewclass': 'MDDropDownItem', 'text': f"{device['name']}", 'on_release': lambda x=device['name']: self.set_output_device(x)} for device in sd.query_devices() if device['max_output_channels'] > 0]

        # Create dropdown menus
        self.input_device_menu = MDDropdownMenu(
            caller=self.ids.input_device_button,
            items=input_devices,
            # position="center",
            width_mult=4
        )
        self.output_device_menu = MDDropdownMenu(
            caller=self.ids.output_device_button,
            items=output_devices,
            # position="center",
            width_mult=4
        )

    def setup_voice_menu(self):
        # List available voices (Example)
        # Replace this with the actual API call to ElevenLabs to list voices
        voices = elevenlabs.voices()
        voice_items = [
            {
                'viewclass': 'MDDropDownItem',
                'text': f"{voice.name}: {voice.labels['accent'] if 'accent' in voice.labels.keys() else None, voice.labels['description'] if 'description' in voice.labels.keys() else None}",
                'on_release': lambda x=voice.voice_id: self.set_voice(x)
            } for voice in voices
        ]

        # Create voice dropdown menu
        self.voice_menu = MDDropdownMenu(
            caller=self.ids.voice_button,
            items=voice_items,
            # position="center",
            width_mult=4
        )

    def set_input_device(self, device_name):
        # Find the device index from the device name
        input_device_index = next((index for index, device in enumerate(sd.query_devices()) if device['name'] == device_name and device['max_input_channels'] > 0), None)
        if input_device_index is not None:
            sd.default.device[0] = input_device_index  # Set as default input
            print(f"Input device set to: {device_name}")
        else:
            print(f"Input device not found: {device_name}")

    def set_output_device(self, device_name):
        # Find the device index from the device name
        output_device_index = next((index for index, device in enumerate(sd.query_devices()) if device['name'] == device_name and device['max_output_channels'] > 0), None)
        if output_device_index is not None:
            sd.default.device[1] = output_device_index  # Set as default output
            print(f"Output device set to: {device_name}")
        else:
            print(f"Output device not found: {device_name}")

    def set_voice(self, voice_id):
        # Set the selected voice ID for use with ElevenLabs
        self.selected_voice_id = voice_id
        print(f"Voice set to: {voice_id}")

    def initialize_chat(self, storyline, character):
        self.persona_agent = PersonaAgent(storyline, character)
        self.ids.transcription_text.text = f"{storyline}\n\n"
        response = self.persona_agent.get_agent_first_response()
        # audio_stream = generate(
        #     text=response,
        #     voice=Voice(
        #             voice_id=self.selected_voice_id,
        #             settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
        #         ),
        #     stream=True
        #     )
        # stream(audio_stream)
        self.ids.transcription_text.text += f"{response}\n\n\n\n"

    def toggle_recording(self):
        if not self.record:
            self.record = True
            self.ids.recording_text.text = 'Recording... Press to Stop'
            self.start_recording()
        else:
            self.record = False
            self.ids.recording_text.text = 'Press to Record'
            self.stop_recording()

    def start_recording(self):
        self.recorded_data = []
        self.stream = sd.InputStream(callback=self.audio_callback, samplerate=self.samplerate, channels=1)
        self.stream.start()

    def stop_recording(self):
        self.stream.stop()
        self.stream.close()

        # Process recorded audio
        recorded_array = np.concatenate(self.recorded_data, axis=0)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        sf.write(temp_file.name, recorded_array, self.samplerate)
        transcript = self.transcribe_audio(temp_file.name)

        # Send transcript as user input to PersonaAgent
        if self.persona_agent and transcript:
            response = self.persona_agent.get_agent_response(transcript)

            audio_stream = generate(
            text=response,
            voice=Voice(
                    voice_id=self.selected_voice_id,
                    settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
                ),
            stream=True
            )
            stream(audio_stream)
            self.ids.transcription_text.text += f"You (Voice): {transcript}\n{self.persona_agent.character}: {response}\n\n\n\n"

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
            print(transcript)
            return transcript

        except Exception as e:
            print('Error')
            return f"An error occurred: {e}"



# Initialize ScreenManager
sm = ScreenManager()
sm.add_widget(FirstScreen(name='first'))
sm.add_widget(SecondScreen(name='second'))

class MyApp(MDApp):
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"  # "Purple", "Red"
        # self.theme_cls.primary_palette = "Blue"
        return Builder.load_file('main.kv')

    def switch_to_second(self):
        self.root.current = 'second'

    def switch_to_first(self):
        self.root.current = 'first'

if __name__ == '__main__':
    MyApp().run()
