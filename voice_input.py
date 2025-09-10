def get_voice_command():
    try:
        import speech_recognition as sr
    except ModuleNotFoundError:
        # Return empty so the app won't proceed; UI can hint installation
        return ""

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎙 Listening... Speak now")
            audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return ""
    except Exception:
        # Likely missing PyAudio or no microphone
        return ""
