import os
import time
import re
import uuid
import asyncio
import threading
import subprocess
import edge_tts

class VoiceOutputManager:
    def __init__(self):
        self.lock = threading.Lock()
        # Ensure temp audio directory exists
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'static', 'temp_audio')
        os.makedirs(self.temp_dir, exist_ok=True)

    def clean_text(self, text):
        """Cleans markdown symbols and whitespace to make speech sound natural."""
        if not text:
            return ""
        # Remove markdown characters (*, #, _, `, ~, -)
        cleaned = re.sub(r'[*#_`~-]', '', text)
        # Remove extra spaces/lines
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def is_hindi_or_hinglish(self, text):
        """Checks if the text contains Devanagari characters or common Hinglish words."""
        # 1. Check for Devanagari characters
        if any(0x0900 <= ord(char) <= 0x097F for char in text):
            print(f"[Backend] Hindi text detected (contains Devanagari characters).")
            return True
            
        # 2. Check for common Hinglish words
        import string
        words = text.lower().translate(str.maketrans('', '', string.punctuation)).split()
        
        HINGLISH_WORDS = {
            "hai", "haan", "ek", "kya", "banna", "kaise", "kyun", "kab", "kahan", "kaun",
            "mera", "meri", "mere", "tum", "aap", "hum", "bhi", "aur", "toh", "ho", "tha",
            "thi", "hoga", "hogi", "honge", "kar", "karo", "karna", "karke", "sath",
            "liye", "kuch", "bahut", "kam", "jyada", "acha", "theek", "sahi", "galat", "gaya",
            "gayi", "gaye", "raha", "rahi", "rahe", "naam", "karta", "karti", "karte", "samajh",
            "soch", "bol", "likh", "padh", "dekh", "chahiye", "karne", "hoke", "bana", "apne",
            "apna", "apni", "unhe", "sakte", "sakta", "sakti", "nhi", "nahi", "sabse", "mujhe",
            "aapka", "aapki", "dhanyawad", "shukriya", "achha", "karlo", "rakhna", "rakho", 
            "lagta", "lagti", "lagte", "karwa", "chal", "chalo", "jao", "aao", "baat", "batao", 
            "bata", "pucho", "puch", "karta", "kiya", "kiye", "kiyi", "mil", "mila", "mile", 
            "milna", "hota", "hoti", "hote", "hona", "sath", "saath", "gaye", "gayi", "gaya",
            "waala", "waali", "waale", "wala", "wali", "wale", "rha", "rhi", "rhe", "hu", "hoon"
        }
        
        if any(word in HINGLISH_WORDS for word in words):
            print(f"[Backend] Hinglish text detected (contains Hinglish words).")
            return True
            
        return False

    def detect_voice(self, text):
        """
        Returns stable English voice.
        Hindi neural voice is disabled temporarily for stability.
        """
        return "en-US-AriaNeural"

    def _generate_edge_tts(self, text, voice, output_path):
        """Helper to run the edge-tts async saving loop inside a dedicated thread."""
        async def _run():
            # Use normal speech speed (rate="+0%")
            communicate = edge_tts.Communicate(text, voice, rate="+0%")
            await communicate.save(output_path)
            
        print(f"[Backend] Starting Edge-TTS audio generation. Voice: {voice}, Rate: +0%, Path: {output_path}")
        result = []
        def _thread_worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_run())
                result.append(True)
            except Exception as e:
                print(f"[Backend] Error in Edge-TTS generation: {e}")
                result.append(False)
            finally:
                loop.close()
                
        t = threading.Thread(target=_thread_worker)
        t.start()
        t.join()
        success = len(result) > 0 and result[0]
        print(f"[Backend] Edge-TTS generation completed. Success: {success}")
        return success

    def speak_text(self, text):
        """Speaks the text aloud on the server's local speakers in a non-blocking thread."""
        if not text:
            return
            
        cleaned_text = self.clean_text(text)
        
        # Hindi voice disabled: return text only instead of broken speech
        if self.is_hindi_or_hinglish(cleaned_text):
            print(f"[Backend] speak_text: Hindi/Hinglish speech output is temporarily disabled. Skipping audio.")
            return
            
        voice = self.detect_voice(cleaned_text)
        
        # Generate a temporary file to play
        temp_filename = f"speak_{uuid.uuid4().hex}.mp3"
        temp_path = os.path.join(self.temp_dir, temp_filename)
        
        print(f"[Backend] speak_text: Scheduling server playback for text: '{cleaned_text[:40]}...'")
        
        def _play_worker():
            success = self._generate_edge_tts(cleaned_text, voice, temp_path)
            if success and os.path.exists(temp_path):
                # Play using Windows MediaPlayer via PowerShell command
                abspath = os.path.abspath(temp_path)
                ps_command = f"""
                Add-Type -AssemblyName PresentationCore
                $player = New-Object System.Windows.Media.MediaPlayer
                $player.Open('{abspath}')
                $player.Play()
                Start-Sleep -Seconds 12
                """
                try:
                    print(f"[Backend] speak_text: Dispatching Windows MediaPlayer command for local playback.")
                    subprocess.run(["powershell", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"[Backend] speak_text: Local playback error: {e}")
                finally:
                    # Clean up file after playback
                    try:
                        os.remove(temp_path)
                        print(f"[Backend] speak_text: Removed temp server audio file: {temp_path}")
                    except Exception:
                        pass
                        
        t = threading.Thread(target=_play_worker)
        t.daemon = True
        t.start()

    def save_speech_to_file(self, text, output_filepath):
        """Saves the speech to an audio file so that the client can play it."""
        if not text:
            return False
            
        cleaned_text = self.clean_text(text)
        
        # Hindi voice disabled: return text only instead of broken speech
        if self.is_hindi_or_hinglish(cleaned_text):
            print(f"[Backend] save_speech_to_file: Hindi/Hinglish speech output is temporarily disabled. Skipping file generation.")
            return False
            
        voice = self.detect_voice(cleaned_text)
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        success = self._generate_edge_tts(cleaned_text, voice, output_filepath)
        return success and os.path.exists(output_filepath)

# Global instance for easy importing
voice_output_manager = VoiceOutputManager()

if __name__ == '__main__':
    # Test local speak
    print("Testing Voice Output with Edge-TTS...")
    voice_output_manager.speak_text("Hello, this is a test of Edge-TTS integration on SmartChat.")
    time.sleep(3)
    
    # Test file saving
    test_filepath = os.path.join(os.path.dirname(__file__), 'static', 'temp_audio', 'temp_test.mp3')
    success = voice_output_manager.save_speech_to_file("Testing saving to file.", test_filepath)
    print(f"File saved successfully: {success} at {test_filepath}")
    if success and os.path.exists(test_filepath):
        os.remove(test_filepath)
