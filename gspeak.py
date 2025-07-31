from gtts import gTTS
import os


def speak_answer_google(answer):
    print(f"CATCAT Answer: {answer}")
    tts = gTTS(answer)
    tts.save("catanswer.mp3")
    os.system("mpg123 -a plughw:1,0 catanswer.mp3")


def main():
    speak_answer_google("I'm a fluffy cat")

if __name__ == "__main__":
    main()
