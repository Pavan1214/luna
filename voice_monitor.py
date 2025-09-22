import asyncio
import time
from audio_fix import audio_manager, restart_audio_engine

class VoiceMonitor:
    def __init__(self):
        self.last_voice_time = 0
        self.voice_timeout = 300  # 5 minutes without voice
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start monitoring voice output"""
        self.monitoring = True
        print("🔊 Voice monitor started")
        
        while self.monitoring:
            await asyncio.sleep(60)  # Check every minute
            
            # If no voice output for timeout period, try to fix
            current_time = time.time()
            if (current_time - self.last_voice_time > self.voice_timeout and 
                self.last_voice_time > 0):  # Only if there was voice before
                
                print("⚠️ Voice output timeout detected, attempting fix...")
                result = await restart_audio_engine()
                print(f"Audio fix result: {result}")
                
                # Update last voice time if fix was successful
                if "✅" in result:
                    self.last_voice_time = current_time
    
    def voice_detected(self):
        """Call this when voice output is successful"""
        self.last_voice_time = time.time()
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring = False

# Global voice monitor instance
voice_monitor = VoiceMonitor()

# Modify the audio_fix.py speak function to update voice monitoring
def speak_with_monitoring(text):
    """Enhanced speak function that updates voice monitoring"""
    success = audio_manager.speak(text)
    if success:
        voice_monitor.voice_detected()
    return success

# Replace the original speak method in AudioManager
audio_manager.speak = speak_with_monitoring