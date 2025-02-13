import gradio as gr
# from gtts import gTTS
import os
from transformers import pipeline
import numpy as np
from db import ChromaVectorStore
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import io
import voice
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("API_KEY")
TRANSFER_TO_HUMAN_DISTANCE_THRESH = 1.3

class BotResponse(BaseModel):
    answer: str
    transfer_to_human: bool = Field(description = "If the answer is not found, set False")


client = genai.Client(api_key=api_key)


VECTOR_DB = ChromaVectorStore('./wise_db')

transcribed_text = ""  

def generate_response():
    global transcribed_text
    results = VECTOR_DB.retrieve(transcribed_text)

    docs = results['documents']

    context = docs[0]

    if results['distances'][0][0] > TRANSFER_TO_HUMAN_DISTANCE_THRESH:
        response = "I'm unable to answer that question as it falls outside my current knowledge domain. Please contact a human agent for further assistance."
    else:
        #  Generate Response using LLM
        prompt = f'''
            You are a helpful customer support assistant. Your task is to answer user questions based ONLY on the provided documents . Follow these rules:

                1. **Answer based on the documents**: Use only the information provided in the documents to answer the question. Do not make up or assume anything outside the documents.
                2. **Be concise**: Provide a clear and concise answer.
                
                Here is the document:
                ---
                {context}
                ---

                Question: {transcribed_text}
        '''

        response = client.models.generate_content(
            model='gemini-2.0-flash-001', 
            contents= prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                response_mime_type='application/json',
                response_schema=BotResponse
            ),
        )

        response = response.parsed.answer

    print ("Response", response)
    bot_voice = voice.text_to_speech(response)
    return response, bot_voice


# Speech Recognition
transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-base.en")

def transcribe(audio):
    global transcribed_text
    sr, y = audio
    
    # Convert to mono if stereo
    if y.ndim > 1:
        y = y.mean(axis=1)
        
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))

    transcribed_text = transcriber({"sampling_rate": sr, "raw": y})["text"] 
    return  transcribed_text




# Gradio Interface
audio_input = gr.Audio(sources="microphone", type="filepath")
out_text = gr.Textbox(label="Bot Response")
out_audio = gr.Audio(label="Voice Response")


with gr.Blocks() as demo:
    gr.Markdown("## Wise Customer Support Agent")
    
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(sources="microphone", type="numpy", label="Record Your Voice")
            output_text = gr.Textbox(label="Audio Text")
            response_btn = gr.Button("Generate Response")
        with gr.Column():
            response_text_output = gr.Textbox(label="Generated Response")
            response_audio_output = gr.Audio(label="Generated Audio")
    
    audio_input.stop_recording(transcribe, inputs=audio_input, outputs=[output_text])
    response_btn.click(generate_response , outputs=[response_text_output, response_audio_output])

demo.launch()