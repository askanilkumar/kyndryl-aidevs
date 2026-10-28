import time

import pandas as pd
import streamlit as st

from agentlib import config, memory


def render(ctx):
    u, s = ctx["user"], ctx["session"]
    st.header("3 · Memory Inspector")
    st.caption("This is Redis. Look for the three rules: the **user id in every key**, a **TTL on every key**, and **trimmed history**.")
    left, right = st.columns(2)

    with left:
        st.subheader("Short-term memory (the chat)")
        st.code(memory.chat_key(u, s), language="text")
        hist = memory.get_history(u, s)
        if not hist:
            st.info("Empty. Add a message, or run a question in tab 4.")
        for m in hist:
            st.markdown(f"**{m['role']}**: {m['content']}")
        txt = st.text_input("Add a message", "My phone number is 9876543210 and my internet is slow", key="mem_msg")
        c = st.columns(3)
        if c[0].button("➕ Add as user"):
            from agentlib import guard
            memory.add_message(u, s, "user", guard.mask_pii(txt))
            st.rerun()
        n = c[1].number_input("Keep last N", 2, 30, config.MAX_MESSAGES, key="mem_n")
        if c[2].button("✂️ Add 15 msgs (N=" + str(int(n)) + ")"):
            for i in range(15):
                memory.add_message(u, s, "user", f"filler message {i}", max_messages=int(n))
            st.rerun()
        st.caption("Notice: the phone number was masked BEFORE it was saved. Never store what you do not need.")

    with right:
        st.subheader("Long-term memory (facts)")
        st.code(memory.profile_key(u), language="text")
        prof = memory.get_profile(u)
        st.json(prof or {"(empty)": ""})
        k, v = st.columns(2)
        key = k.text_input("Fact name", "language")
        val = v.text_input("Fact value", "Tamil")
        if st.button("💾 Save fact"):
            memory.set_profile(u, **{key: val})
            st.rerun()
        st.caption("Facts live for weeks. Chat lives for minutes. Choose each number on purpose.")

    st.subheader("Every key in Redis (all customers)")
    rows = memory.inspect_keys()
    if rows:
        df = pd.DataFrame(rows)
        df["owner"] = df["key"].str.split(":").str[1]
        st.dataframe(df, width="stretch", hide_index=True)
    c = st.columns(3)
    if c[0].button("⏱️ Set a 10-second TTL on this chat"):
        memory.get_redis().expire(memory.chat_key(u, s), 10)
        st.session_state["ttl_demo"] = time.time()
        st.rerun()
    if c[1].button("🔄 Refresh TTLs"):
        st.rerun()
    if c[2].button("🗑️ Forget this customer (erase everything)"):
        n = memory.forget_user(u)
        st.success(f"Deleted {n} key(s). That is the 'right to be forgotten' in one line.")
        st.rerun()
    st.caption("TTL = Time To Live. When it hits zero, Redis deletes the key by itself. Press Refresh to watch it count down.")
