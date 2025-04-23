import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import os
import pickle

COURSE_FILES = [
    "enriched_undergraduate_courses.json",
    "enriched_postgraduate_courses2.json"
]
OUTPUT_DIR = "faiss_course_store"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_and_prepare_data():
    combined_data = []
    for file in COURSE_FILES:
        with open(file, "r", encoding="utf-8") as f:
            combined_data.extend(json.load(f))

    docs = []
    for entry in combined_data:
        metadata = {
            "title": entry.get("title", ""),
            "url": entry.get("url", ""),
            "type": entry.get("programme_type", "Course")
        }
        for key, value in entry.items():
            if key not in metadata and isinstance(value, str):
                docs.append(Document(page_content=value.strip(), metadata=metadata))
    return docs

def main():
    print("📥 Loading & embedding course data...")
    docs = load_and_prepare_data()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    print(f"Number of chunks: {len(split_docs)}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    vectorstore.save_local(OUTPUT_DIR)
    with open(os.path.join(OUTPUT_DIR, "docs.pkl"), "wb") as f:
        pickle.dump(split_docs, f)

    print("✅ Course data indexed and saved!")

if __name__ == "__main__":
    main()
