import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://sims.texsar.org"

# ------------------------
# LOGIN FUNCTION
# ------------------------
def login(email, password):
    session = requests.Session()

    # Step 1 — GET login page
    r = session.get(BASE + "/login", headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        st.error("Could not find CSRF token (_token) in login page.")
        st.code(r.text[:500])
        return None, "CSRF token missing"

    csrf_token = token_input["value"]

    # Step 2 — Submit login POST exactly like browser
    payload = {
        "_token": csrf_token,
        "email": email,
        "password": password
    }

    headers = {
        "Referer": BASE + "/login",
        "Origin": BASE,
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    login_resp = session.post(BASE + "/login", data=payload, headers=headers)

    # Check if login succeeded
    if "laravel_session" not in session.cookies:
        return None, "Login failed — check credentials."

    return session, None


# ------------------------
# FETCH PERSONNEL DATA
# ------------------------
def fetch_personnel(session, limit=25):
    # Full DataTables params (must match browser exactly)
    params = {
        "draw": 1,
        "columns[0][data]": "preferred_full_name",
        "columns[0][name]": "",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "true",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",

        "columns[1][data]": "team_email",
        "columns[1][name]": "",
        "columns[1][searchable]": "true",
        "columns[1][orderable]": "true",
        "columns[1][search][value]": "",
        "columns[1][search][regex]": "false",

        "columns[2][data]": "division",
        "columns[2][name]": "divisions.name",
        "columns[2][searchable]": "true",
        "columns[2][orderable]": "true",
        "columns[2][search][value]": "",
        "columns[2][search][regex]": "false",

        "columns[3][data]": "certs",
        "columns[3][name]": "",
        "columns[3][searchable]": "false",
        "columns[3][orderable]": "true",
        "columns[3][search][value]": "",
        "columns[3][search][regex]": "false",

        "columns[4][data]": "status",
        "columns[4][name]": "",
        "columns[4][searchable]": "true",
        "columns[4][orderable]": "true",
        "columns[4][search][value]": "",
        "columns[4][search][regex]": "false",

        "columns[5][data]": "actions",
        "columns[5][name]": "",
        "columns[5][searchable]": "true",
        "columns[5][orderable]": "true",
        "columns[5][search][value]": "",
        "columns[5][search][regex]": "false",

        "order[0][column]": 0,
        "order[0][dir]": "asc",
        "order[0][name]": "",

        "start": 0,
        "length": limit,
        "search[value]": "",
        "search[regex]": "false",
        "division": 0,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": BASE + "/personnel",
        "X-Requested-With": "XMLHttpRequest"
    }

    resp = session.get(BASE + "/personnel/data", params=params, headers=headers)

    # Debug if not JSON
    if resp.status_code != 200:
        st.error(f"Error fetching personnel data: {resp.status_code}")
        st.code(resp.text[:500])
        return None

    try:
        json_data = resp.json()
    except Exception:
        st.error("Response was not JSON. Here's the first part of it:")
        st.code(resp.text[:500])
        return None

    return pd.DataFrame(json_data.get("data", []))


# ------------------------
# STREAMLIT UI
# ------------------------
st.title("TEXSAR Personnel Scraper")

email = st.text_input("TEXSAR Email")
password = st.text_input("TEXSAR Password", type="password")

limit = st.number_input("Number of entries", min_value=1, max_value=500, value=100)

if st.button("Login & Fetch Personnel"):
    with st.spinner("Logging in..."):
        session, error = login(email, password)

    if error:
        st.error(error)
    else:
        st.success("Login successful!")

        with st.spinner("Fetching personnel data..."):
            df = fetch_personnel(session, limit)

        if df is None or df.empty:
            st.error("No data returned. Check logs above.")
        else:
            st.success("Data loaded successfully!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "personnel.csv", mime="text/csv")
