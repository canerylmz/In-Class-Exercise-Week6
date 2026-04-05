from flask import Flask, render_template, request
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

app = Flask(__name__)

OUTPUT_FOLDER = os.path.join("static", "outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/text-to-speech", methods=["POST"])
def text_to_speech():
    text = request.form.get("text", "").strip()

    if not text:
        return render_template("index.html", error="Lütfen bir metin girin.")

    speech_key = os.getenv("SPEECH_KEY")
    speech_region = os.getenv("SPEECH_REGION")

    if not speech_key or not speech_region:
        return render_template("index.html", error="SPEECH_KEY veya SPEECH_REGION bulunamadı.")

    output_file = os.path.join(OUTPUT_FOLDER, "output.wav")

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )

        speech_config.speech_synthesis_voice_name = "en-US-Ava:DragonHDLatestNeural"

        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return render_template(
                "index.html",
                success="Speech synthesized successfully!",
                audio_file=output_file
            )
        else:
            return render_template("index.html", error="Ses oluşturulamadı.")

    except Exception as e:
        return render_template("index.html", error=f"Hata oluştu: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)