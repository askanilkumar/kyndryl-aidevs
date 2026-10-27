"""CHECKPOINT 1 - the empty app: title, question box, button.
Copy to the lab folder as app_basic.py and run:  python -m streamlit run app_basic.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):      # lets this file run from this folder or from the lab folder
    sys.path.insert(0, p)

import streamlit as st

st.set_page_config(page_title="NetNova Help", page_icon="📶")
st.title("📶 NetNova Help")
st.caption("Ask a question about plans, roaming, billing or SIM.")

question = st.text_input("Your question")
if st.button("Ask") and question:
    st.write("You asked:", question)
