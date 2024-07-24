import os
import google.generativeai as genai

from prompts import summaryPrompt

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')


def summarize(raw_transcript):
	genai.configure(api_key=GOOGLE_API_KEY)
	model = genai.GenerativeModel('gemini-pro')
	prompt = summaryPrompt(raw_transcript)
	response = model.generate_content(prompt)
	return response.text
