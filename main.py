from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import tempfile
import assemblyai as aai
from gemini import summarize

app = Flask(__name__)
CORS(app,
     resources={
         r"/*": {
             "origins":
             ["https://transcribe.emmetts.dev", "https://*.emmetts.dev"]
         }
     })
aai.settings.api_key = os.environ.get('ASSEMBLY_API_KEY')

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the QuickTranscribe API"})

@app.route('/transcribe', methods=['POST'])
def transcribe_route():
    if 'file' not in request.files:
        return jsonify({'error': 'no file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'no file selected'}), 400

    filename = secure_filename(file.filename)

    # Define the upload directory
    UPLOAD_DIR = '/uploads'
    # Create a custom temporary directory within the persistent storage
    temp_dir = tempfile.mkdtemp(dir=UPLOAD_DIR)

    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)

    try:
        result_file = process_file(file_path)
        return send_file(result_file,
                         as_attachment=True,
                         download_name=os.path.basename(result_file))
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        temp_dir.cleanup()
        os.rmdir(temp_dir)

def process_file(file_url):
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speech_model=aai.SpeechModel.best,
        filter_profanity=False,
        entity_detection=True,
        iab_categories=True,
        auto_highlights=True,
        sentiment_analysis=True
    )

    print("Transcribing audio...")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_url, config)


    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+') as temp_file:
        
        temp_file.write("\n\n----------------\n\n")
        
        temp_file.write("Transcript:\n\n")

        for utterance in transcript.utterances:
            temp_file.write(f"SPEAKER {utterance.speaker}: {utterance.text}\n")

        temp_file.write("\n\n----------------\n\n")

        temp_file.write("\nSummary:\n" + summarize(transcript.text) + "\n")

        temp_file.write("\n\n----------------\n\n")

        temp_file.write("\nHighlights:\n")
        if transcript.auto_highlights and hasattr(transcript.auto_highlights, 'result') and transcript.auto_highlights.result is not None:
            for highlight in transcript.auto_highlights.result:
                temp_file.write(f" - {highlight.text}\n")
        else:
            temp_file.write("No highlights available.\n")


        temp_file.write("\n\n----------------\n\n")

        temp_file.write("Names & Resources Detected:\n")
        for entity in transcript.entities:
            entity_type_string = entity.entity_type.split('.')[-1]
            temp_file.write(f" - {entity_type_string.upper()}, {entity.text}\n")

        temp_file.write("\n\n----------------\n\n")

        temp_file.write("Topics:\n")
        for topic, relevance in transcript.iab_categories.summary.items():
            temp_file.write(f" - {topic.split('>')[-1]}, Relevance: {relevance * 100:.1f}%\n")

        temp_file.write("\n\n----------------\n\n")

        sentiments = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
        for sentiment in transcript.sentiment_analysis:
            sentiments[sentiment.sentiment] += 1
        temp_file.write("Sentiment Summary:\n")
        temp_file.write(f"Positive sentences: {sentiments['POSITIVE']}, ")
        temp_file.write(f"Negative sentences: {sentiments['NEGATIVE']}, ")
        temp_file.write(f"Neutral sentences: {sentiments['NEUTRAL']}\n")
        
        temp_file.write("\n\n----------------\n\n\n")

    return temp_file.name

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
