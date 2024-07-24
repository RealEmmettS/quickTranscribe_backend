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

		if file:
				filename = secure_filename(file.filename)
				temp_dir = tempfile.TemporaryDirectory()
				file_path = os.path.join(temp_dir.name, filename)
				file.save(file_path)

				try:
						result_file = process_file(file_path)
						return send_file(result_file,
														 as_attachment=True,
														 download_name=os.path.basename(result_file))
				finally:
						temp_dir.cleanup()

		return jsonify({'error': 'An unexpected error occurred'}), 500

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

		# Debug print to inspect the structure
		print(transcript.auto_highlights.__dict__)

		with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+') as temp_file:
				temp_file.write("Transcript:\n" + transcript.text + "\n")
				temp_file.write("\nSummary:\n" + summarize(transcript.text) + "\n")

				temp_file.write("\nHighlights:\n")
				if hasattr(transcript.auto_highlights, 'result'):
						for highlight in transcript.auto_highlights.result:
								temp_file.write(f" - {highlight.text}\n")
				else:
						temp_file.write("No highlights available.\n")

				temp_file.write("\nEntities Detected:\n")
				for entity in transcript.entities:
						temp_file.write(
								f"{entity.text} ({entity.entity_type}) [Start: {entity.start}, End: {entity.end}]\n"
						)

				temp_file.write("\nTopics:\n")
				for topic, relevance in transcript.iab_categories.summary.items():
						temp_file.write(f"Topic: {topic}, Relevance: {relevance * 100}%\n")

				sentiments = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
				for sentiment in transcript.sentiment_analysis:
						sentiments[sentiment.sentiment] += 1
				temp_file.write("\nSentiment Summary:\n")
				temp_file.write(f"Positive sentences: {sentiments['POSITIVE']}, ")
				temp_file.write(f"Negative sentences: {sentiments['NEGATIVE']}, ")
				temp_file.write(f"Neutral sentences: {sentiments['NEUTRAL']}\n")

		return temp_file.name

if __name__ == '__main__':
		app.run(host='0.0.0.0', port=5000)