from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from db import ChromaVectorStore
from google import genai
from google.genai import types
import uvicorn

db = ChromaVectorStore('./wise_db')
app = FastAPI()
client = genai.Client(api_key='AIzaSyAMdkObKnAqIAw8myvwhPsyR47mjLhnH-s')


class Query(BaseModel):
    text: str

class BotResponse(BaseModel):
    answer: str
    transfer_to_human: bool = Field(description = "If the answer is not found, set False")

@app.post("/query")
async def handle_query(query: Query):
    try:
        # Retreive relevant docs based on query
        results = db.retrieve(query.text)
        docs = results['documents']
        context = docs[0]
        #  Generate Response
        prompt = f'''
            You are a helpful customer support assistant. Your task is to answer user questions based ONLY on the provided documents. Follow these rules:

                1. **Answer based on the documents**: Use only the information provided in the documents to answer the question. Do not make up or assume anything outside the documents.
                2. **Be concise**: Provide a clear and concise answer.

                Here is the document:
                ---
                {context}
                ---

                Question: {query.text}
        '''

        print (prompt)
        response = client.models.generate_content(
            model='gemini-2.0-flash-001', 
            contents= prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                response_mime_type='application/json',
                response_schema=BotResponse
            ),
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)