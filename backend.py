import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv

load_dotenv()

COURSE_VECTOR_PATH = "./faiss_course_store"
FAQ_VECTOR_PATH = "./faiss_faq_store"
EMBED_MODEL = "all-MiniLM-L6-v2"

def load_vectorstore(folder):
    index = faiss.read_index(f"{folder}/faiss.index")
    with open(f"{folder}/docs.pkl", "rb") as f:
        docs = pickle.load(f)
    docstore = InMemoryDocstore({str(i): doc for i, doc in enumerate(docs)})
    return FAISS(
        embedding_function=SentenceTransformer(EMBED_MODEL).encode,
        index=index,
        docstore=docstore,
        index_to_docstore_id={i: str(i) for i in range(len(docs))}
    )

def get_retrievers(topics):
    metadata_filter = {"topics": {"$in": topics}} if topics else {}
    faq_vectorstore = load_vectorstore(FAQ_VECTOR_PATH)
    course_vectorstore = load_vectorstore(COURSE_VECTOR_PATH)
    retriever_faq = faq_vectorstore.as_retriever(search_kwargs={"k": 1, "filter": metadata_filter})
    retriever_course = course_vectorstore.as_retriever(search_kwargs={"k": 5, "filter": metadata_filter})
    return retriever_faq, retriever_course

def build_context(faq_docs, course_docs):
    context = ""
    if faq_docs:
        for doc in faq_docs:
            context += f"FAQ:\n{doc.page_content.strip()}\n\n"
    if course_docs:
        for doc in course_docs:
            context += f"Document:\n{doc.page_content.strip()}\n\n"
    return context.strip()

def get_qa_chain():
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)

    prompt = PromptTemplate.from_template("""
Use the context below to answer the question. If the context includes the answer, provide it in a friendly and detailed way. If the context is missing important details, say you don’t know.

Context:
{context}

Question:
{question}

Answer:
""")


    def run_hybrid(inputs):
        question = inputs["question"]
        topics = inputs.get("topics", [])

        retriever_faq, retriever_course = get_retrievers(topics)
        faq_docs = retriever_faq.get_relevant_documents(question)
        course_docs = retriever_course.get_relevant_documents(question)

        context = build_context(faq_docs, course_docs)
        answer = llm.invoke(prompt.format(context=context, question=question)).content

        source_list = []
        for doc in (faq_docs + course_docs):
            source_list.append({
                "source": doc.metadata.get("source", ""),
                "title": doc.metadata.get("title", "Unknown")
            })

        return answer, source_list

    return RunnableLambda(run_hybrid)