"""CHECKPOINT 2 - load the knowledge base and show it in the sidebar."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):      # lets this file run from this folder or from the lab folder
    sys.path.insert(0, p)

import streamlit as st
from rag.kb import load_kb

st.set_page_config(page_title="NetNova Help", page_icon="📶")


@st.cache_resource
def get_docs():
    return load_kb()


docs = get_docs()
with st.sidebar:
    st.header("Knowledge base")
    st.write(f"{len(docs)} documents loaded")
    for d in docs:
        st.caption(f"{d.id} - {d.title}")

st.title("📶 NetNova Help")
question = st.text_input("Your question")
if st.button("Ask") and question:
    st.write("You asked:", question)
