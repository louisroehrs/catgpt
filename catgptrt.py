#!/usr/bin/env python3
"""
CatGPT Realtime - Voice conversation using OpenAI's Whisper + GPT + TTS APIs
Listens to microphone input, transcribes with Whisper, gets GPT response, and plays back with TTS
"""

import asyncio
import json
import base64
import pyaudio
import wave
import threading
import time
import os
import subprocess
import numpy as np
from openai import OpenAI

# Configuration
# OPENAI_API_KEY = 'your-api-key-here'  # Replace with your actual API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = "gpt-4o"  # Using regular GPT-4o for text generation
AUDIO_FILENAME = "temp_audio.wav"
SAMPLE_RATE = 16000  # 16 kHz for Whisper transcription
CHUNK = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16
MIC_INDEX = 1  # Adjust based on your microphone

class CatGPTRealtime:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.is_playing = False
        self.audio_buffer = []
        
    def setup_audio(self):
        """Initialize audio input/output"""
        print("Setting up audio...")
        
        # Check available audio devices
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
    
    def record_audio_chunk(self, duration=1.0):
        """Record audio for a specified duration"""
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=MIC_INDEX,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for _ in range(0, int(SAMPLE_RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        return b''.join(frames)
    
    def save_audio_to_file(self, audio_data, filename):
        """Save audio data to WAV file"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data)
    
    def play_audio_file(self, filename):
        """Play audio file using system audio player"""
        try:
            # Use mpg123 if available, otherwise try other players
            subprocess.run(['mpg123', '-a', 'plughw:1,0', filename], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fallback to aplay for WAV files
                subprocess.run(['aplay', filename], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("No suitable audio player found. Please install mpg123 or aplay.")
    
    def text_to_speech(self, text):
        """Convert text to speech and play it"""
        print(f"CatGPT: {text}")
        
        # Use gTTS for text-to-speech
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save("response.mp3")
            self.play_audio_file("response.mp3")
            os.remove("response.mp3")  # Clean up
        except ImportError:
            print("gTTS not available. Install with: pip install gtts")
            # Fallback to system TTS
            try:
                subprocess.run(['espeak', text], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("No TTS available. Text response only.")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function to process audio input."""
        if status:
            print(f"Audio error: {status}")
        # Convert audio input to bytes
        audio_data = indata.tobytes()
        # Store audio data for processing
        self.audio_buffer.append(audio_data)

    async def send_audio_to_openai(self, audio_data):
        """Send audio data to OpenAI for transcription and get text response."""
        try:
            # Save audio to temporary file
            temp_audio_file = "temp_input.wav"
            self.save_audio_to_file(audio_data, temp_audio_file)
            
            # Transcribe audio using Whisper
            with open(temp_audio_file, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            print(f"You said: {transcript}")
            
            # Get response from GPT with voice output
            try:
                # Try the new voice response API if available
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful cat assistant. Keep responses brief and friendly."},
                        {"role": "user", "content": transcript}
                    ],
                    stream=True,
                    response_format={"type": "voice"}  # Try voice response format
                )
                
                # Handle voice response
                await self.handle_voice_response(response)
                
            except Exception as voice_error:
                print(f"Voice response not available, falling back to text: {voice_error}")
                
                # Fallback to text response with TTS
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful cat assistant. Keep responses brief and friendly."},
                        {"role": "user", "content": transcript}
                    ],
                    stream=True
                )
                
                # Stream the response and convert to speech
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        print(content, end="", flush=True)
                
                print()  # New line after streaming
                
                # Convert full response to speech using OpenAI TTS
                await self.text_to_speech_openai(full_response)
            
            # Clean up temp file
            os.remove(temp_audio_file)
            
        except Exception as e:
            print(f"OpenAI API error: {e}")

    async def handle_voice_response(self, response):
        """Handle voice response from chat completions API."""
        try:
            audio_chunks = []
            for chunk in response:
                # Check if chunk contains voice/audio data
                if hasattr(chunk.choices[0].delta, 'voice') and chunk.choices[0].delta.voice:
                    # Handle voice data if available
                    voice_data = chunk.choices[0].delta.voice
                    if hasattr(voice_data, 'data'):
                        audio_chunks.append(voice_data.data)
                elif hasattr(chunk.choices[0].delta, 'audio') and chunk.choices[0].delta.audio:
                    # Handle audio data if available
                    audio_data = chunk.choices[0].delta.audio
                    if hasattr(audio_data, 'data'):
                        audio_chunks.append(audio_data.data)
                elif chunk.choices[0].delta.content:
                    # Fallback to text if voice not available
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
            
            if audio_chunks:
                # Combine and play audio chunks
                combined_audio = b''.join(audio_chunks)
                audio_array = np.frombuffer(combined_audio, dtype=np.int16)
                self.play_audio_data(audio_array)
            else:
                print()  # New line after text streaming
                
        except Exception as e:
            print(f"Voice response error: {e}")

    async def text_to_speech_openai(self, text):
        """Convert text to speech using OpenAI TTS API."""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
                response_format="mp3"
            )
            
            # Save the audio response
            audio_file = "response.mp3"
            with open(audio_file, "wb") as f:
                f.write(response.content)
            
            # Play the audio
            self.play_audio_file(audio_file)
            
            # Clean up
            os.remove(audio_file)
            
        except Exception as e:
            print(f"TTS error: {e}")
            # Fallback to gTTS
            self.text_to_speech(text)

    def play_audio_data(self, audio_data):
        """Play audio data directly"""
        try:
            # Use sounddevice for better audio playback
            import sounddevice as sd
            sd.play(audio_data, samplerate=SAMPLE_RATE)
            sd.wait()
        except ImportError:
            # Fallback to saving and playing file
            self.save_audio_to_file(audio_data.tobytes(), "response.wav")
            self.play_audio_file("response.wav")
            os.remove("response.wav")

    async def process_audio_buffer(self):
        """Process accumulated audio data"""
        while True:
            if len(self.audio_buffer) > 0:
                # Combine all buffered audio
                combined_audio = b''.join(self.audio_buffer)
                self.audio_buffer.clear()
                
                # Only process if we have enough audio data (at least 1 second)
                if len(combined_audio) >= SAMPLE_RATE * 2:  # 2 seconds of audio
                    # Send to OpenAI
                    await self.send_audio_to_openai(combined_audio)
            
            await asyncio.sleep(0.5)  # Check every 500ms

    async def realtime_conversation(self):
        """Main realtime conversation loop using 2025 API"""
        print("Starting realtime conversation with CatGPT...")
        print("Press Ctrl+C to exit")
        
        try:
            # Use sounddevice for better audio handling
            import sounddevice as sd
            
            print("Setting up audio stream...")
            
            # Start audio processing task
            audio_task = asyncio.create_task(self.process_audio_buffer())
            
            with sd.InputStream(
                samplerate=SAMPLE_RATE, 
                channels=CHANNELS, 
                dtype=np.int16, 
                callback=self.audio_callback
            ):
                print("Listening... Press Ctrl+C to stop.")
                try:
                    await asyncio.sleep(3600)  # Run for 1 hour or until interrupted
                except KeyboardInterrupt:
                    print("Stopped.")
                    
        except ImportError:
            print("sounddevice not available, falling back to PyAudio...")
            # Fallback to PyAudio method
            await self.fallback_conversation()
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

    async def fallback_conversation(self):
        """Fallback conversation using PyAudio"""
        print("Using PyAudio fallback method...")
        while True:
            print("\nListening... (speak now)")
            
            # Record audio
            audio_data = self.record_audio_chunk(duration=3.0)
            
            # Send to OpenAI and get response
            await self.send_audio_to_openai(audio_data)
            
            # Small delay before next iteration
            await asyncio.sleep(1.0)
    
    def cleanup(self):
        """Clean up resources"""
        self.audio.terminate()
        # Clean up any temporary files
        for filename in [AUDIO_FILENAME, "response.wav", "response.mp3"]:
            if os.path.exists(filename):
                os.remove(filename)

def main():
    """Main function"""
    print("CatGPT Voice Assistant - Whisper + GPT + TTS")
    print("=" * 50)
    
    # Check if API key is set
    if not OPENAI_API_KEY:
        print("ERROR: Please set your OpenAI API key in the OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Create and run the realtime assistant
    catgpt = CatGPTRealtime()
    catgpt.setup_audio()
    
    try:
        asyncio.run(catgpt.realtime_conversation())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
=======
import openai
import sounddevice as sd
# import numpy as np
import queue
import base64

import ctypes
import contextlib
import speech_recognition as sr
import openai
import time
import os
from gtts import gTTS


print ("Running catgptrt.py")

SAMPLERATE = 44000

# Set env OPENAI_API_KEY variable in your environment
client = openai.OpenAI()


# Initialize recognizer class (for recognizing speech)
recognizer = sr.Recognizer()


def listen_for_question():
    # Use the USB microphone for audio input
    mic = sr.Microphone(device_index=1)

    with mic as source:
        print("Listening for a question...")

        # Adjust for ambient noise
#        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 200
        # Listen for the audio and record it
        audio = recognizer.listen(source)

        try:
            # Recognize speech using Google Speech Recognition
            print("CATCAT Recognizing...")
            question = recognizer.recognize_openai(audio)
            print(f"CATCAT Question: {question}")
            if question =="you":
                return None
            return question
        except sr.UnknownValueError:
            print("CATCAT Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            print("CATCAT Could not request results from Google Speech Recognition service.")
            return None

# realtime
def ask_gpt_and_speak_response (question):
    with client.chat.completions.stream(
            model="gpt-4o",
            modalities= ["text","audio"],
            audio = {"format" : "pcm16", "voice" : "verse"},
            messages = [{"role": "user", "content": question}]
            ) as stream:
                for event in stream:
                    if event.type == "response.output_audio.delta":
#                        pcm_bytes = event.delta
#                        audio_array = np.frombuffer(pcm_bytes, dtype=np.int16)
                        sd.play(event.delta) # , samplerate = SAMPLERATE)
                        sd.wait()

    
def ask_chatgpt(question):
    try:
        response = openai.responses.create(
            model="gpt-3.5-turbo",

            instructions = "You are a helpful fluffy cat.  With every response, ask a question to another fluffy cat about what they are working on and continue to ask questions relevant to their responses. Please keep the answers on the shorter side.",
            input = question 
        )

        answer = response.output_text
        return answer
    except Exception as e:
        print(f"CATCAT Error contacting OpenAI: {e}")
        return None

def speak_answer_google(answer):
    print(f"CATCAT Answer: {answer}")
    tts = gTTS(answer)
    tts.save("catanswer.mp3")
    os.system("mpg123 -a plughw:1,0 catanswer.mp3")

def say_intro():
    print("CATCAT saying intro")
    os.system("mpg123 -a plughw:1,0 catwelcome2.mp3")

    
def main_old():
    say_intro()
    while True:
        question = listen_for_question()
        if question:
            answer = ask_chatgpt(question)
            if answer:
                speak_answer_google(answer)
        time.sleep(1)  # Avoid continuous loop too fast

def main():
#    say_intro()
    while True:
        question = listen_for_question()
        print(f"Question: {question}")
        if question:
            answer = ask_gpt_and_speak_response(question)
        time.sleep(1)  # Avoid continuous loop too fast


if __name__ == "__main__":
    main()
