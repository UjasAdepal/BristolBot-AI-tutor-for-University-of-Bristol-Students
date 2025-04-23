import streamlit as st
from backend import get_qa_chain
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Bristol AI Tutor", layout="centered")

st.title("🎓 Bristol AI Tutor")
st.caption("Ask anything about the University of Bristol — from admissions to accommodation!")

# ✅ Topic filtering
TOPIC_OPTIONS = [
    "Undergraduate", "Postgraduate", "Student Support", "Accommodation", "International Students",
    "Scholarships", "Fees & Funding", "Library & IT", "Vet School", "Admissions", "Research"
]

selected_topics = st.multiselect("📂 Filter by topic (optional):", TOPIC_OPTIONS)

query = st.text_input("💬 Ask your question here:")

if query:
    with st.spinner("Thinking..."):
        chain = get_qa_chain()
        response, sources = chain.invoke({"question": query, "topics": selected_topics})

    st.subheader("📘 Answer")
    st.write(response)

    if sources:
        with st.expander("🔗 Sources used"):
            for s in sources:
                st.markdown(f"- [{s['title']}]({s['source']})")

    # ✅ Feedback
    st.subheader("👍 Was this helpful?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Yes"):
            st.success("Thanks for your feedback!")
    with col2:
        if st.button("👎 No"):
            st.warning("Sorry! We'll try to improve.")

    # Optional: save feedback to local file
    # with open("feedback_log.txt", "a") as f:
    #     f.write(f"{time.time()} | {query} | {response[:100]}... | feedback: yes/no\n")
