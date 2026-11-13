import re
import streamlit as st

def login_screen():
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='login-eyebrow'>RETAIL INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='login-title'>Welcome back.</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='login-subtitle'>Sign in to view your inventory, sales and demand insights.</p>",
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter any username")
        password = st.text_input("8-digit password", type="password", placeholder="e.g. 12345678")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        if not username.strip():
            st.error("Please enter a username.")
        elif not re.fullmatch(r"\d{8}", password):
            st.error("Password must contain exactly 8 digits.")
        else:
            # Simple demonstration login: any username + any 8-digit numeric password.
            st.session_state["authenticated"] = True
            st.session_state["username"] = username.strip()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Demo authentication only. Any username and any 8-digit numeric password are accepted.")
