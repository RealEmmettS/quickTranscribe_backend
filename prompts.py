

def summaryPrompt(raw_transcription):
	prompt = f"Summarize the following transcription of a conversation, keeping all possibly important information, and disregarding all other conversational banter or 'fluff' information. Consider when summarizing that some speakers noted in the transcript may actually be the same person, but was misheard by the transcription / tts algorithm used. In your responses, do not use markdown; write the summary in plaintext (but please use basic formatting and * for bullet points). The transcription is as follows:\n{raw_transcription}\n"
	return prompt


	