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
