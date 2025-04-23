import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import os
import pickle

FAQ_FILE = "scraped_faq_data.json"
OUTPUT_DIR = "faiss_faq_store"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_and_prepare_faqs():
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    for block in data:
        source = block.get("source", "")
        topics = block.get("topics", [])
        for q in block.get("questions", []):
            question = q.get("question", "").strip()
            answer = q.get("answer", "").strip()
            content = f"Q: {question}\nA: {answer}"
            metadata = {
                "source": source,
                "topics": topics
            }
            docs.append(Document(page_content=content, metadata=metadata))
    return docs

def main():
    print("📥 Loading & embedding FAQ data...")
    docs = load_and_prepare_faqs()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    print(f"Number of chunks: {len(split_docs)}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    vectorstore.save_local(OUTPUT_DIR)
    with open(os.path.join(OUTPUT_DIR, "docs.pkl"), "wb") as f:
        pickle.dump(split_docs, f)

    print("✅ FAQ data indexed and saved!")

if __name__ == "__main__":
    main()
