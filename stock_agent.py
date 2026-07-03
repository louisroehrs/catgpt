#!/usr/bin/env python3
"""
Stock Analysis Agent - Shows biggest stock gainers over the last week
Uses Alpha Vantage API for stock data and OpenAI for analysis
"""

import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
import asyncio
import pyaudio
import wave
import numpy as np
import sounddevice as sd
from gtts import gTTS
import subprocess

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')  # Get free key from https://www.alphavantage.co/support/#api-key
SAMPLE_RATE = 16000
CHUNK = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16
MIC_INDEX = 1

class StockAgent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.audio = pyaudio.PyAudio()
        self.audio_buffer = []
        
    def get_weekly_gainers(self, limit=10):
        """Get the biggest stock gainers over the last week"""
        try:
            # Get top gainers from Alpha Vantage
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TOP_GAINERS_LOSERS',
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'top_gainers' in data:
                gainers = data['top_gainers'][:limit]
                
                # Process and format the data
                formatted_gainers = []
                for stock in gainers:
                    formatted_gainers.append({
                        'symbol': stock['ticker'],
                        'price': f"${float(stock['price']):.2f}",
                        'change': f"${float(stock['change_amount']):.2f}",
                        'change_percent': f"{float(stock['change_percentage']):.2f}%",
                        'volume': f"{int(stock['volume']):,}"
                    })
                
                return formatted_gainers
            else:
                print("Error fetching data:", data)
                return []
                
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            return []
    
    def get_stock_analysis(self, gainers_data):
        """Get AI analysis of the stock gainers"""
        try:
            # Format data for AI analysis
            data_text = "Top Stock Gainers This Week:\n\n"
            for i, stock in enumerate(gainers_data, 1):
                data_text += f"{i}. {stock['symbol']}: {stock['price']} ({stock['change_percent']})\n"
            
            # Get AI analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Analyze stock market data and provide insights about the biggest gainers. Keep responses concise and informative."},
                    {"role": "user", "content": f"Analyze these stock gainers and provide insights:\n\n{data_text}"}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting AI analysis: {e}")
            return "Unable to analyze stock data at this time."
    
    def display_stock_data(self, gainers_data, analysis):
        """Display stock data in a formatted table"""
        print("\n" + "="*80)
        print("📈 BIGGEST STOCK GAINERS - LAST WEEK")
        print("="*80)
        
        # Create DataFrame for nice formatting
        df = pd.DataFrame(gainers_data)
        df.index = range(1, len(df) + 1)
        
        print(df.to_string(index=True))
        
        print("\n" + "="*80)
        print("🤖 AI ANALYSIS")
        print("="*80)
        print(analysis)
        print("="*80)
    
    def text_to_speech(self, text):
        """Convert text to speech"""
        try:
            tts = gTTS(text=text, lang='en')
            tts.save("stock_response.mp3")
            subprocess.run(['mpg123', '-a', 'plughw:1,0', 'stock_response.mp3'], check=True)
            os.remove("stock_response.mp3")
        except Exception as e:
            print(f"TTS error: {e}")
    
    def record_audio(self, duration=3):
        """Record audio from microphone"""
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
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper"""
        try:
            # Save audio to temporary file
            temp_file = "temp_audio.wav"
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)
            
            # Transcribe
            with open(temp_file, 'rb') as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text"
                )
            
            os.remove(temp_file)
            return transcript.strip()
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    def process_voice_command(self, command):
        """Process voice command and respond"""
        print(f"You said: {command}")
        
        # Check if command is about stocks
        stock_keywords = ['stock', 'gainer', 'gainers', 'market', 'stocks', 'ticker', 'price']
        if any(keyword in command.lower() for keyword in stock_keywords):
            print("\nFetching stock data...")
            gainers = self.get_weekly_gainers()
            
            if gainers:
                analysis = self.get_stock_analysis(gainers)
                self.display_stock_data(gainers, analysis)
                
                # Create voice response
                response_text = f"Here are the top stock gainers this week. {analysis[:200]}..."
                self.text_to_speech(response_text)
            else:
                error_msg = "Sorry, I couldn't fetch the stock data at this time."
                print(error_msg)
                self.text_to_speech(error_msg)
        else:
            response_text = "I can help you with stock market information. Ask me about stock gainers, market trends, or specific tickers."
            print(response_text)
            self.text_to_speech(response_text)
    
    def run_interactive_mode(self):
        """Run interactive voice mode"""
        print("🎤 Stock Agent Voice Mode")
        print("Say 'show me stock gainers' or 'what are the biggest gainers'")
        print("Press Ctrl+C to exit")
        
        try:
            while True:
                print("\nListening... (speak now)")
                
                # Record audio
                audio_data = self.record_audio(duration=3)
                
                # Transcribe
                transcript = self.transcribe_audio(audio_data)
                
                if transcript:
                    self.process_voice_command(transcript)
                else:
                    print("Could not understand audio. Please try again.")
                
                # Small delay
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.cleanup()
    
    def run_text_mode(self):
        """Run text mode for direct queries"""
        print("📊 Stock Agent Text Mode")
        print("Type 'gainers' to see biggest stock gainers, or 'quit' to exit")
        
        try:
            while True:
                command = input("\nEnter command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() in ['gainers', 'gainer', 'stocks']:
                    print("\nFetching stock data...")
                    gainers = self.get_weekly_gainers()
                    
                    if gainers:
                        analysis = self.get_stock_analysis(gainers)
                        self.display_stock_data(gainers, analysis)
                    else:
                        print("Sorry, I couldn't fetch the stock data at this time.")
                else:
                    print("I can help you with stock market information. Try 'gainers' to see the biggest stock gainers.")
                    
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.audio.terminate()
        # Clean up temp files
        for filename in ["temp_audio.wav", "stock_response.mp3"]:
            if os.path.exists(filename):
                os.remove(filename)

def main():
    """Main function"""
    print("📈 Stock Analysis Agent")
    print("=" * 50)
    
    # Check API keys
    if not OPENAI_API_KEY:
        print("ERROR: Please set your OpenAI API key")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    if not ALPHA_VANTAGE_API_KEY:
        print("ERROR: Please set your Alpha Vantage API key")
        print("Get free key from: https://www.alphavantage.co/support/#api-key")
        print("export ALPHA_VANTAGE_API_KEY='your-api-key-here'")
        return
    
    agent = StockAgent()
    
    # Choose mode
    print("\nChoose mode:")
    print("1. Voice mode (speak commands)")
    print("2. Text mode (type commands)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            agent.run_interactive_mode()
        elif choice == "2":
            agent.run_text_mode()
        else:
            print("Invalid choice. Running text mode...")
            agent.run_text_mode()
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

