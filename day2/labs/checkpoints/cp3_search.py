"""CHECKPOINT 3 - cut into chunks, embed, store in Qdrant, show the top 3 matches."""
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
st.caption(f"Mode: {llm.mode_name()}  |  {len(index.chunks)} chunks in Qdrant")

question = st.text_input("Your question")
if st.button("Ask") and question:
    qvec = llm.embed([question])[0]
    hits = index.vector(qvec, k=3)
    st.subheader("Top matches")
    for chunk, score in hits:
        st.markdown(f"**{chunk.doc_id}** - similarity {score:.2f}")
        st.write(chunk.text)
