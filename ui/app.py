"""
ui/app.py
=========
Streamlit chatbot UI that connects to Databricks Genie.
Run with:  streamlit run ui/app.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from src.genie_api import ask_genie, validate_credentials

# ── Page config ───────────────────────────────────────────────────────────────
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "Genie SQL Chatbot")

st.set_page_config(
    page_title=CHATBOT_NAME,
    page_icon="🧞",
    layout="centered",
)

# ── Sidebar — credentials status ─────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Connection")
    ok, err = validate_credentials()
    if ok:
        st.success("✅ Credentials loaded")
        st.caption(f"Space ID: `{os.getenv('GENIE_SPACE_ID','')[:12]}...`")
    else:
        st.error(f"❌ {err}")
        st.info("Fill in your `config/.env` file and restart.")

    st.divider()
    st.markdown("**Example questions**")
    examples = [
        "Total trips in the dataset?",
        "Top 5 pickup zones by trip count?",
        "Average fare amount?",
        "Busiest hour of the day?",
        "Average trip distance in miles?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state["prefill"] = q

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state["messages"] = []

# ── Chat history initialisation ───────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"🧞 {CHATBOT_NAME}")
st.caption("Ask any question about your data — Genie writes the SQL and returns the answer.")

# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("📄 SQL Genie wrote"):
                st.code(msg["sql"], language="sql")

# ── Input — support prefill from sidebar buttons ──────────────────────────────
prefill = st.session_state.pop("prefill", "")
user_input = st.chat_input(
    "Ask anything about your data...",
    disabled=not ok,
)

question = user_input or (prefill if prefill else None)

# ── Send question to Genie ────────────────────────────────────────────────────
if question:
    # Show user message
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Call Genie and show spinner
    with st.chat_message("assistant"):
        with st.spinner("Genie is writing the SQL and fetching the answer..."):
            result = ask_genie(question)

        if result["status"] == "error":
            reply = f"❌ **Error:** {result['error']}"
            st.error(result["error"])
            st.session_state["messages"].append({
                "role": "assistant",
                "content": reply,
                "sql": "",
            })
        else:
            answer = result["answer"] or "✅ Query ran — no text answer returned."
            sql    = result["sql"]

            st.markdown(answer)
            if sql:
                with st.expander("📄 SQL Genie wrote"):
                    st.code(sql, language="sql")

            st.session_state["messages"].append({
                "role": "assistant",
                "content": answer,
                "sql": sql,
            })
