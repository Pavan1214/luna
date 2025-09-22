import pyttsx3
import sounddevice as sd
import speech_recognition as sr
from pygame import mixer
import tempfile
import os
from langchain.tools import tool
import numpy as np

class AudioManager:
    def __init__(self):
        self.engine = None
        self.setup_audio()
        
    def setup_audio(self):
        """Initialize audio engine with proper settings"""
        try:
            # Initialize text-to-speech engine
            self.engine = pyttsx3.init()
            
            # Get available voices and select a good one
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voices if available, they're often clearer
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Fallback to first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 180)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            
            print(f"✅ Audio engine initialized with voice: {self.engine.getProperty('voice')}")
            
        except Exception as e:
            print(f"❌ Failed to initialize audio engine: {e}")
            self.engine = None
    
    def speak(self, text):
        """Speak text using text-to-speech"""
        if not self.engine:
            print("Audio engine not available")
            return False
            
        try:
            # Stop any ongoing speech
            self.engine.stop()
            
            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"❌ Speech synthesis failed: {e}")
            self.setup_audio()  # Try to reinitialize
            return False

# Global audio manager instance
audio_manager = AudioManager()

@tool
async def check_audio_output() -> str:
    """
    Checks and fixes audio output issues for Jarvis voice.
    
    Use this tool when Jarvis stops speaking but still responds textually.
    Example prompts:
    - "ఆడియో సమస్యను పరిష్కరించండి"
    - "Voice పని చేయడం లేదు"
    - "Audio issue fix చేయండి"
    """
    
    results = []
    
    # 1. Check audio devices
    try:
        devices = sd.query_devices()
        results.append(f"🔊 Found {len(devices)} audio devices")
    except Exception as e:
        results.append(f"❌ Audio device query failed: {e}")
    
    # 2. Test basic audio playback
    try:
        # Generate a simple test tone
        sample_rate = 44100
        duration = 1.0  # seconds
        frequency = 440  # Hz (A4 note)
        
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        sd.play(tone, sample_rate)
        sd.wait()
        results.append("✅ Test tone played successfully")
    except Exception as e:
        results.append(f"❌ Test tone failed: {e}")
    
    # 3. Check TTS engine
    if audio_manager.engine:
        voices = audio_manager.engine.getProperty('voices')
        results.append(f"✅ TTS engine working with {len(voices)} voices")
    else:
        results.append("❌ TTS engine not initialized")
    
    # 4. Try to speak a test message
    test_message = "ఆడియో పరీక్ష సందేశం. జార్విస్ వాయిస్ పని చేస్తుంది."
    if audio_manager.speak(test_message):
        results.append("✅ Voice synthesis working")
    else:
        results.append("❌ Voice synthesis failed")
    
    return "\n".join(results)

@tool
async def restart_audio_engine() -> str:
    """
    Restarts the audio engine completely to fix voice output issues.
    
    Use this when Jarvis has completely lost voice output capability.
    Example prompts:
    - "ఆడియో ఇంజిన్ రీస్టార్ట్ చేయండి"
    - "Voice system restart చేయండి"
    - "Audio reset చేయండి"
    """
    
    global audio_manager
    audio_manager = AudioManager()
    
    if audio_manager.engine:
        test_message = "ఆడియో ఇంజిన్ పునఃప్రారంభించబడింది. జార్విస్ వాయిస్ పని చేస్తుంది."
        audio_manager.speak(test_message)
        return "✅ Audio engine restarted successfully"
    else:
        return "❌ Failed to restart audio engine"

@tool
async def set_audio_volume(level: int = 80) -> str:
    """
    Sets the audio volume level for Jarvis voice output.
    
    Args:
        level (int): Volume level from 0 to 100
        
    Example prompts:
    - "వాయిస్ వాల్యూమ్ 80కి సెట్ చేయండి"
    - "Volume increase చేయండి"
    - "Sound తగ్గించండి"
    """
    
    if not audio_manager.engine:
        return "❌ Audio engine not available"
    
    # Validate volume level
    level = max(0, min(100, level))
    volume = level / 100.0
    
    try:
        audio_manager.engine.setProperty('volume', volume)
        audio_manager.speak(f"వాల్యూమ్ స్థాయి {level}కి సెట్ చేయబడింది")
        return f"✅ Volume set to {level}%"
    except Exception as e:
        return f"❌ Failed to set volume: {e}"