"""CHECKPOINT 5 - the finished basic app: who is asking, example questions, 'I don't know' guard, sources with scores."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):      # lets this file run from this folder or from the lab folder
    sys.path.insert(0, p)

import streamlit as st
from rag.kb import load_kb, chunk_docs
from rag.index import Index
from rag import llm

st.set_page_config(page_title="NetNova Help", page_icon="📶", layout="wide")

ROLES = {"Postpaid customer": "postpaid", "Prepaid customer": "prepaid", "NOC engineer": "noc"}
EXAMPLES = ["How much data does Postpaid Max include?", "How long do I have to dispute a bill?",
            "What does error code E-4107 mean?", "Which cafeteria serves vegan food on Fridays?"]


@st.cache_resource
def get_index():
    return Index(chunk_docs(load_kb(), "section"))


index = get_index()

with st.sidebar:
    st.header("Settings")
    who = st.selectbox("Who is asking?", list(ROLES))
    top_k = st.slider("Chunks to send to the model (top-k)", 1, 8, 3)
    guard = st.slider("Say 'I don't know' below this similarity", 0.0, 0.6, 0.28 if llm.online() else 0.30, 0.01)
    st.caption(f"Mode: {llm.mode_name()}")

st.title("📶 NetNova Help")
st.caption("Answers come only from the NetNova knowledge base.")

if "q" not in st.session_state:
    st.session_state.q = ""
cols = st.columns(len(EXAMPLES))
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex):
        st.session_state.q = ex
question = st.text_input("Your question", key="q")

if st.button("Ask", type="primary") and question:
    hits = index.vector(llm.embed([question])[0], k=top_k, role=ROLES[who], only_current=True)
    best = hits[0][1] if hits else 0.0
    if best < guard:
        st.warning("I don't know based on the knowledge base.")
        st.caption(f"Best similarity was {best:.2f}, below your limit of {guard:.2f}.")
    else:
        chunks = [{"text": c.text, "doc_id": c.doc_id} for c, _ in hits]
        with st.spinner("Thinking..."):
            reply = llm.answer(question, chunks, grounded=True)
        st.subheader("Answer")
        st.write(reply)
    with st.expander("Sources and scores"):
        for chunk, score in hits:
            st.markdown(f"**{chunk.doc_id}** | similarity {score:.2f}")
            st.caption(chunk.text)
