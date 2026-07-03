#!/usr/bin/env python3
"""
CatGPT Fluffy - Realtime speech-to-speech voice agent for the Raspberry Pi.

Design for a Raspberry Pi 2 (weak CPU, no GPU): the Pi is only a thin client.
All the heavy lifting (STT + LLM + TTS) happens in the cloud in a single
OpenAI Realtime API WebSocket session. The Pi just:

    mic  ->  (idle) local wake-word "fluffy cat"
         ->  stream PCM audio to the Realtime API
         <-  stream PCM audio back and play it on the speaker

Wake word keeps us from streaming audio (and paying) 24/7. While idle we do a
cheap local recognizer pass looking for the phrase "fluffy cat". Once heard we
open a realtime session and converse until a silence timeout, then go back to
sleep.

Env vars:
    OPENAI_API_KEY   required
    CATGPT_MODEL     realtime model (default: gpt-realtime-mini)
    CATGPT_VOICE     voice name (default: verse)
    MIC_INDEX        input device index (default: 1, the USB mic)

Deps: pip install openai websockets pyaudio SpeechRecognition
"""

import os
import sys
import json
import base64
import queue
import threading
import asyncio

import pyaudio
import websockets
import speech_recognition as sr

# --- Configuration ---------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("CATGPT_MODEL", "gpt-realtime-mini")
VOICE = os.getenv("CATGPT_VOICE", "verse")
MIC_INDEX = int(os.getenv("MIC_INDEX", "1"))

WAKE_WORD = "fluffy cat"
REALTIME_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"

# Realtime API speaks PCM16 mono @ 24 kHz for both input and output.
SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 2400  # 100 ms of audio per chunk

SYSTEM_PROMPT = (
    "You are Fluffy, a friendly, helpful cat assistant. Answer the user's "
    "questions clearly and concisely. Keep spoken replies on the shorter side "
    "and stay in a warm, playful cat persona without overdoing the meowing."
)

# How long a silence (server VAD) ends the whole conversation and returns to
# wake-word listening.
CONVERSATION_IDLE_SECONDS = 20


# --- Wake word (local, cheap) ---------------------------------------------
def wait_for_wake_word():
    """Block until the user says the wake word. Runs locally on the Pi.

    Uses SpeechRecognition's free Google recognizer for a quick phrase check.
    Swap recognize_google for recognize_sphinx (pocketsphinx) if you want a
    fully offline wake word with no network dependency while idle.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    mic = sr.Microphone(device_index=MIC_INDEX)

    print(f'Sleeping. Say "{WAKE_WORD}" to wake me up...')
    while True:
        with mic as source:
            audio = recognizer.listen(source, phrase_time_limit=4)
        try:
            heard = recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"Wake-word recognizer error: {e}")
            continue
        print(f"Heard: {heard}")
        if WAKE_WORD in heard:
            print("Wake word detected!")
            return


# --- Realtime conversation -------------------------------------------------
class RealtimeSession:
    """One speech-to-speech conversation over the OpenAI Realtime API."""

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.play_queue = queue.Queue()
        self.stop = threading.Event()
        self.last_audio_activity = threading.Event()

    def _playback_worker(self):
        """Pull PCM chunks off the queue and play them on the speaker."""
        out = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
        )
        while not self.stop.is_set():
            try:
                chunk = self.play_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if chunk is None:
                break
            out.write(chunk)
        out.stop_stream()
        out.close()

    async def _send_mic(self, ws):
        """Stream microphone audio to the Realtime API."""
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=MIC_INDEX,
            frames_per_buffer=CHUNK,
        )
        try:
            while not self.stop.is_set():
                data = await asyncio.to_thread(stream.read, CHUNK, False)
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(data).decode("ascii"),
                }))
        finally:
            stream.stop_stream()
            stream.close()

    async def _receive(self, ws):
        """Handle events coming back from the Realtime API."""
        async for message in ws:
            event = json.loads(message)
            etype = event.get("type")

            if etype == "response.output_audio.delta":
                # Streamed spoken audio -> playback queue.
                self.play_queue.put(base64.b64decode(event["delta"]))

            elif etype == "response.output_audio_transcript.done":
                print(f"Fluffy: {event.get('transcript', '')}")

            elif etype == "conversation.item.input_audio_transcription.completed":
                print(f"You: {event.get('transcript', '')}")

            elif etype == "error":
                print(f"Realtime error: {event.get('error')}")

    async def run(self):
        """Open the session, configure it, and converse until idle timeout."""
        playback = threading.Thread(target=self._playback_worker, daemon=True)
        playback.start()

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        async with websockets.connect(REALTIME_URL, additional_headers=headers) as ws:
            # Configure the session: audio in/out, server-side VAD for turn
            # detection, transcription of the user's speech, and our persona.
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": SYSTEM_PROMPT,
                    "voice": VOICE,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "silence_duration_ms": 500,
                    },
                },
            }))

            print("Listening... (say something, or stay quiet to go back to sleep)")

            sender = asyncio.create_task(self._send_mic(ws))
            receiver = asyncio.create_task(self._receive(ws))

            # End the conversation after a stretch of no activity. We treat the
            # receiver going quiet plus a wall-clock idle timeout as "done".
            try:
                await asyncio.wait_for(
                    asyncio.gather(sender, receiver),
                    timeout=CONVERSATION_IDLE_SECONDS,
                )
            except asyncio.TimeoutError:
                pass
            finally:
                self.stop.set()
                sender.cancel()
                receiver.cancel()

        self.play_queue.put(None)
        playback.join(timeout=2)

    def close(self):
        self.audio.terminate()


def main():
    if not OPENAI_API_KEY:
        print("ERROR: set OPENAI_API_KEY in your environment.")
        sys.exit(1)

    print("CatGPT Fluffy - Realtime voice agent")
    print("=" * 40)

    while True:
        try:
            wait_for_wake_word()
            session = RealtimeSession()
            try:
                asyncio.run(session.run())
            finally:
                session.close()
            print("Going back to sleep.\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
