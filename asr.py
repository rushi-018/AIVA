"""
asr.py: Minimal ASR (Automatic Speech Recognition) module for AIVA
- Uses SpeechRecognition + fallback to text input
- Provides get_text_input() and get_voice_input() functions
- get_command() chooses best available (voice, else text)
"""
import logging
from typing import Optional

def get_text_input(prompt: str = "Type your command: ") -> str:
    return input(prompt)

def get_voice_input(timeout: int = 5) -> Optional[str]:
    try:
        import speech_recognition as sr
    except ImportError:
        logging.warning("SpeechRecognition not installed. Falling back to text input.")
        return None
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎙 Listening... Speak now")
            audio = r.listen(source, timeout=timeout)
        try:
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
    except Exception as e:
        logging.warning(f"Voice input unavailable: {e}")
        return None

def get_command() -> str:
    """Try voice input, else fallback to text input."""
    text = get_voice_input()
    if text:
        print(f"You said: {text}")
        return text
    else:
        return get_text_input()

if __name__ == "__main__":
    print("AIVA ASR Demo: Speak or type a command.")
    cmd = get_command()
    print(f"Command received: {cmd}")
