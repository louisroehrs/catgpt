import openai
import pyaudio
import wave
import pyttsx3
import time
import subprocess

## See ~/.asoundrc for mic configuration

openai.api_key = ' key '
model = "gpt-3.5-turbo"
AUDIO_FILENAME = "input.wav"
RECORD_SECONDS = 4
SAMPLE_RATE = 44100
CHUNK = 8000
CHANNELS = 1
FORMAT = pyaudio.paInt16
MIC_INDEX = 1

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate',150)
    engine.say(text)
    engine.runAndWait()


def record_audio():
    print("Record audio")
    p = pyaudio.PyAudio()

    print("recording...")
    stream  = p.open( format = FORMAT,
                      channels = CHANNELS,
                      rate = SAMPLE_RATE,
                      input = True,
                      input_device_index=MIC_INDEX,
                      frames_per_buffer=CHUNK)
    frames = []

    for _ in range(0, int (SAMPLE_RATE/ CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(AUDIO_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_audio():
    print("Transcribing")
    with open(AUDIO_FILENAME, 'rb') as f:
        transcript = opanai.Audio.transcribe("whisper-1", f)
        return transcript['text']

    
def ask_chatgpt(prompt):
    print("Sending to ChatGPT...")
    response = openai.ChatCompletion.create(
        model = model,
        message = [
            {"role": "system", "content":"You are a helpful assistant."},
            {"role": "user", "content": prompt }
        ]
    )
    answer = response['choices'][0]['message']['content']
    return answer.strip()


def main():
    print("Cat assistant ready. Press Ctrl+C to exit.")
    while True:
        record_audio()
        try:
            prompt = transcribe_audio()
            print( f"You said: {user_input} ")

        except Exception as e:
            print(f"Transcription failed")
            continue
        
        gpt_response = ask_chatgpt(user_input)
        print( f"CatGPT: {gpt_response}")
        speak(gpt_response)
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Exiting. Good bye!")


        
             
