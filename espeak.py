import pyttsx3
import time

# Initialize text-to-speech engine
engine = pyttsx3.init()


def speak_answer(answer):
    print(f"CATCAT Answer: {answer}")
    engine.setProperty("volume",1)
    engine.say(answer)
    engine.runAndWait()

def main():
    speak_answer("I'm a fluffy cat")

if __name__ == "__main__":
    main()
