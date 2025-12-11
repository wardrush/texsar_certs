import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://sims.texsar.org"


def login(email, password):
    session = requests.Session()

    # 1. Load login page -> extract Laravel token
    resp = session.get(BASE + "/login")
    soup = BeautifulSoup(resp.text, "html.parser")

    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        return None, "Could not find Laravel _token."

    token = token_input["value"]

    # 2. Send login request
    payload = {
        "_token": token,
        "email": email,
        "password": password,
    }

    resp = session.post(BASE + "/login", data=payload)

    # If cookies aren’t set → login failed
    if "laravel_session" not in session.cookies:
        return None, "Login failed — check credentials."

    return session, None


def fetch_personnel(session, limit):
    params = {
        "draw": 1,
        "start": 0,
        "length": limit,
        "division": 0
    }

    resp = session.get(BASE + "/personnel/data", params=params)
    
    if resp.status_code != 200:
        return None

    data = resp.json().get("data", [])
    return pd.DataFrame(data)


# ---------------------------
# STREAMLIT UI
# ---------------------------

st.title("TEXSAR Personnel Data Scraper")

email = st.text_input("TEXSAR Email")
password = st.text_input("TEXSAR Password", type="password")

limit = st.number_input("Number of personnel to pull", min_value=1, max_value=500, value=100)

if st.button("Login & Fetch Data"):
    with st.spinner("Logging in..."):
        session, error = login(email, password)

    if error:
        st.error(error)
    else:
        st.success("Login successful!")

        with st.spinner("Fetching personnel data..."):
            df = fetch_personnel(session, limit)

        if df is None or df.empty:
            st.error("No data returned.")
        else:
            st.success("Data loaded!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode()
            st.download_button(
                "Download CSV",
                csv,
                file_name="personnel.csv",
                mime="text/csv"
            )