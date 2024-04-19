from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import tempfile
from gemini import summarize
import assemblyai as aai

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": ["https://transcribe.emmetts.dev", "https://*.emmetts.dev"]}})

aai.settings.api_key = os.environ['ASSEMBLY_API_KEY']

@app.route('/transcribe', methods=['POST'])
def transcribe_route():
		# Ensure a file is present in the request
		if 'file' not in request.files:
				return jsonify({'error': 'no file provided'}), 400

		file = request.files['file']

		# Ensure the file has a name
		if file.filename == '':
				return jsonify({'error': 'no file selected'}), 400

		# Save the uploaded file to a temporary directory
		if file:
				filename = secure_filename(file.filename)
				temp_dir = tempfile.TemporaryDirectory()
				file_path = os.path.join(temp_dir.name, filename)
				file.save(file_path)

				# Call the existing transcribe function
				try:
						temp_file = transcribe_file(file_path)

						# Return the transcript as a download
						return send_file(
							temp_file.name,
							as_attachment=True,
							download_name=os.path.basename(temp_file.name)
						)
				finally:
						# Cleanup
						temp_dir.cleanup()

		return jsonify({'error': 'An unexpected error occurred'}), 500

def transcribe_file(file_url):
		config = aai.TranscriptionConfig(speaker_labels=True, speech_model=aai.SpeechModel.best, filter_profanity=False, disfluencies=True)

		print("Transcribing audio...")
		with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+') as temp_file:
				transcriber = aai.Transcriber()
				transcript = transcriber.transcribe(
						file_url,
						config=config
				)

				print("Saving transcription to file...")
				to_summarize = ""
				for utterance in transcript.utterances:
						temp_file.write(f"\nSpeaker {utterance.speaker}: {utterance.text}\n")
						to_summarize += f"\nSpeaker {utterance.speaker}: {utterance.text}\n"

				print("Adding transcription summary...")
				summary = summarize(to_summarize)
				temp_file.write(f"\n\n-----\n\nSummary: {summary}\n")
				temp_file.flush()
				os.fsync(temp_file.fileno())
				print("Complete.")
				return temp_file

if __name__ == '__main__':
		app.run(host='0.0.0.0', port=5000, debug=False)