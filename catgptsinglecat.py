import ctypes
import contextlib
import sounddevice  #removes ALSA error logging
import speech_recognition as sr
import openai
import logging
import time
import os
from gtts import gTTS

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger("Fluffy cat")

# Set env OPENAI_API_KEY variable in your environment

# Initialize recognizer class (for recognizing speech)
recognizer = sr.Recognizer()


def listen_for_question():
    # Use the USB microphone for audio input
    mic = sr.Microphone(device_index=1)

    with mic as source:
        logger.info("Listening for a question...")

        # Adjust for ambient noise
#        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 200
        # Listen for the audio and record it
        audio = recognizer.listen(source)

        try:
            # Recognize speech using Open AI Speech Recognition
            logger.info("Recognizing...")
            question = recognizer.recognize_openai(audio)
            logger.info(f"Question: {question}")
            if question =="you":

                return None
            return question
        except sr.UnknownValueError:
            logger.info("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            logger.info("Could not request results from Google Speech Recognition service.")
            return None

def ask_chatgpt(question):
    try:
        response = openai.responses.create(
            model="gpt-5-nano",

            instructions = "You are a helpful fluffy cat named Lorenzo.  Start by asking a question about what they are working on and continue to ask questions relevant to their responses. Please keep the answers on the shorter side.",
            input = question 
        )

        answer = response.output_text
        return answer
    except Exception as e:
        logger.info(f"Error contacting OpenAI: {e}")
        return None

def speak_answer_google(answer):
    logger.info(f"Answer: {answer}")
    tts = gTTS(answer)
    tts.save("catanswer.mp3")
    os.system("mpg123 -a plughw:1,0 catanswer.mp3")

def say_intro():
    logger.info("Saying intro")
    os.system("mpg123 -a plughw:1,0 catwelcome2.mp3")

    
def main():
    say_intro()
    while True:
        question = listen_for_question()
        if question:
            answer = ask_chatgpt(question)
            if answer:
                speak_answer_google(answer)
        time.sleep(1)  # Avoid continuous loop too fast

if __name__ == "__main__":
    main()
