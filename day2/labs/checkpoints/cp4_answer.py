"""CHECKPOINT 4 - send the matches to the LLM and show a real answer with its sources."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):      # lets this file run from this folder or from the lab folder
    sys.path.insert(0, p)

import streamlit as st
from rag.kb import load_kb, chunk_docs
from rag.index import Index
from rag import llm

st.set_page_config(page_title="NetNova Help", page_icon="📶")


@st.cache_resource
def get_index():
    docs = [d for d in load_kb() if d.status == "current"]
    return Index(chunk_docs(docs, "section"))


index = get_index()
st.title("📶 NetNova Help")
st.caption(f"Mode: {llm.mode_name()}")

question = st.text_input("Your question")
if st.button("Ask") and question:
    hits = index.vector(llm.embed([question])[0], k=3)
    chunks = [{"text": c.text, "doc_id": c.doc_id} for c, _ in hits]
    with st.spinner("Thinking..."):
        reply = llm.answer(question, chunks, grounded=True)
    st.subheader("Answer")
    st.write(reply)
    with st.expander("Sources used"):
        for chunk, score in hits:
            st.markdown(f"**{chunk.doc_id}** ({score:.2f}): {chunk.text}")
