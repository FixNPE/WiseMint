"""FinAdvisor — Streamlit chat interface."""
from __future__ import annotations

import os

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.agent import orchestrator
from src.safety import input_guard, output_filter

st.set_page_config(
    page_title="FinAdvisor",
    page_icon="💹",
    layout="centered",
)

st.title("💹 FinAdvisor")
st.caption("Educational financial guidance powered by AI — not financial advice.")

# Session state
if "history" not in st.session_state:
    st.session_state.history = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "streamlit_user"

# Render conversation history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a financial question…"):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})

    # Safety check
    safe, reason = input_guard.check(prompt)
    if not safe:
        response = (
            input_guard.DISTRESS_RESPONSE
            if reason == "distress"
            else "I'm sorry, I can't process that request."
        )
    else:
        with st.spinner("Thinking…"):
            raw = orchestrator.run(
                prompt,
                user_id=st.session_state.user_id,
                history=st.session_state.history[:-1],
            )
        response = output_filter.filter_output(raw)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.history.append({"role": "assistant", "content": response})

# Sidebar: user profile + portfolio chart
with st.sidebar:
    st.header("Your Profile")
    age = st.number_input("Current age", 18, 90, 35)
    retirement_age = st.number_input("Retirement age", 40, 90, 65)
    monthly_savings = st.number_input("Monthly savings ($)", 0, 100000, 500)

    if st.button("Update profile"):
        from src.memory.profile_db import update_profile
        update_profile(st.session_state.user_id, {
            "age": age,
            "retirement_age": retirement_age,
            "monthly_savings": monthly_savings,
        })
        st.success("Profile saved!")

    st.divider()
    st.header("Quick Portfolio Chart")
    tickers_input = st.text_input("Tickers & weights (e.g. AAPL:60,MSFT:40)")
    if tickers_input:
        try:
            pairs = [p.split(":") for p in tickers_input.split(",")]
            labels = [p[0].strip().upper() for p in pairs]
            values = [float(p[1]) for p in pairs]
            fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4))
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
            st.plotly_chart(fig, use_container_width=True)
        except (ValueError, IndexError):
            st.error("Format: TICKER:weight,TICKER:weight")
