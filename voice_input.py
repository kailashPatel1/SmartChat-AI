import speech_recognition as sr
import os

class VoiceInputManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust recognizer settings for ambient noise and sensitivity
        self.recognizer.dynamic_energy_threshold = True

    def listen_from_mic(self, timeout=5, phrase_time_limit=10):
        """
        Listens to the server's local microphone and transcribes it to text.
        Useful for running and testing the app locally on a machine with a microphone.
        """
        try:
            # We check if Microphone is available (requires PyAudio)
            # If PyAudio is not installed, this will throw an error
            with sr.Microphone() as source:
                print("Adjusting for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening... Speak now.")
                
                # Listen to source
                audio_data = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                print("Processing speech...")
                
                # Perform transcription
                text = self.recognizer.recognize_google(audio_data)
                print(f"Transcribed Text: {text}")
                return {
                    'success': True,
                    'text': text,
                    'error': None
                }
        except sr.WaitTimeoutError:
            return {
                'success': False,
                'text': '',
                'error': 'Listening timed out. No speech detected.'
            }
        except sr.UnknownValueError:
            return {
                'success': False,
                'text': '',
                'error': 'Could not understand the audio.'
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'text': '',
                'error': f'Speech recognition service error: {e}'
            }
        except OSError as e:
            # Typically PyAudio or microphone system access error
            return {
                'success': False,
                'text': '',
                'error': f'Microphone access error: {e}. Please ensure a microphone is connected and PyAudio is installed.'
            }
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'error': f'An unexpected error occurred: {str(e)}'
            }

    def transcribe_audio_file(self, audio_filepath):
        """
        Transcribes an audio file (e.g. WAV uploaded by the browser) to text.
        This allows full web-based speech recognition on the server.
        """
        if not os.path.exists(audio_filepath):
            return {
                'success': False,
                'text': '',
                'error': f'Audio file not found: {audio_filepath}'
            }
            
        try:
            with sr.AudioFile(audio_filepath) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                return {
                    'success': True,
                    'text': text,
                    'error': None
                }
        except sr.UnknownValueError:
            return {
                'success': False,
                'text': '',
                'error': 'Speech recognition could not understand the audio file.'
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'text': '',
                'error': f'Speech recognition service error: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'error': f'Error transcribing audio file: {str(e)}'
            }

# Global instance for easy importing
voice_input_manager = VoiceInputManager()

if __name__ == '__main__':
    # Test local microphone transcription if run directly
    print("Testing Voice Input (Mic)... Press Ctrl+C to cancel.")
    result = voice_input_manager.listen_from_mic()
    print("Result:", result)
