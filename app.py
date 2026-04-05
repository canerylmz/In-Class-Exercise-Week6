from flask import Flask, render_template, request, jsonify
import os
import uuid
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("stt.html")

@app.route("/save-recording", methods=["POST"])
def save_recording():
    recorded_audio = request.files.get("recorded_audio")

    if not recorded_audio:
        return jsonify({"success": False, "message": "No recording received"})

    original_name = recorded_audio.filename or ""
    extension = os.path.splitext(original_name)[1].lower() or ".wav"
    unique_name = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    recorded_audio.save(file_path)

    return jsonify({"success": True, "filename": unique_name})

@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    speech_key = os.getenv("SPEECH_KEY")
    speech_region = os.getenv("SPEECH_REGION")

    if not speech_key or not speech_region:
        return render_template("stt.html", error="SPEECH_KEY or SPEECH_REGION is missing.")

    uploaded_file = request.files.get("audio")
    recorded_audio_name = request.form.get("recorded_audio_name", "").strip()

    file_path = None

    if uploaded_file and uploaded_file.filename != "":
        file_extension = os.path.splitext(uploaded_file.filename)[1].lower() or ".wav"
        filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(file_path)

    elif recorded_audio_name:
        file_path = os.path.join(UPLOAD_FOLDER, recorded_audio_name)

    else:
        return render_template("stt.html", error="Please upload or record an audio file.")

    try:
        supported_extensions = {".wav", ".mp3", ".ogg", ".flac", ".opus"}
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension not in supported_extensions:
            return render_template(
                "stt.html",
                error="Unsupported audio format. Please upload or record a WAV, MP3, OGG, FLAC, or OPUS file."
            )

        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )

        audio_config = speechsdk.audio.AudioConfig(filename=file_path)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return render_template(
                "stt.html",
                success="Audio transcribed successfully!",
                transcript=result.text
            )

        elif result.reason == speechsdk.ResultReason.NoMatch:
            return render_template("stt.html", error="No speech could be recognized.")

        else:
            return render_template("stt.html", error="Speech recognition failed.")

    except Exception as e:
        return render_template("stt.html", error=f"Error: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
