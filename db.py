import chromadb as db
from chromadb.utils import embedding_functions
import numpy as np
import json

class ChromaVectorStore:
    def __init__(self, persist_directory: str = None):
        """
        Initialize the ChromaDB vector store. If a persist_directory is provided,
        it loads the existing database; otherwise, it creates a new one.
        """
        self.client = db.PersistentClient(path=persist_directory) if persist_directory else db.Client()
        self.collection = self.client.get_or_create_collection(name="vector_store")
    
    def add_to_store(self, documents: list, ids: list):
        """
        Add documents to the vector store with associated IDs.
        """
        self.collection.add(ids=ids, documents=documents)
    
    def retrieve(self, query: str, top_k: int = 2):
        """
        Retrieve the top_k most relevant documents based on the query.
        """
        results = self.collection.query(query_texts=[query], n_results=top_k)
        return results
    
if __name__ == '__main__':
    v_db = ChromaVectorStore('./wise_db')

    # with open('md.txt', 'r', encoding="utf-8") as f:
    #     txt = f.read()
    #     txt = txt.replace("\xa0", " ")
    
    # data = json.loads(txt)

    # for k, v in data.items():
    #     print (f"Adding to DB : {k}")
    #     v_db.add_to_store([v], [k])

    questions = [
        # "How long does it usually take for money to arrive?",
        # "Why is my transfer taking longer than expected?",
        # "How will I know when the money arrives?",
        # "What is the status of my transfer?",
        # "Is my money delayed?",
        # "Why hasn't my money arrived yet?",
        # "Can you tell me where my money is?",
        # "How do I track my transfer?",
        # "What's the expected delivery time for my transfer?",
        # "Why is my transfer still pending?",
        # "My transfer was supposed to arrive yesterday, but it hasn’t. What’s going on?"
        # Specific Questions
        "I sent money to my friend, but they haven’t received it. What should I do?",
        "Why is my transfer taking more than 2 days?",
        "How can I check the status of my transfer?",
        "Will I get a notification when the money arrives?",
        "What happens if my transfer is delayed?",
        "Why is my transfer stuck in processing?",
        "Can you explain why my transfer is taking so long?",
        "What are the reasons for a delayed transfer?",
        "How do I know if my transfer has been completed?"
    ]

    for q in questions:
        print (q, '---------------------')
        results = v_db.retrieve(query=q)
        # print (results)
        print (results['documents'][0])
        break
        # print (results['distances'])
        # print (results['ids'])