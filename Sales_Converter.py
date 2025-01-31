import streamlit as st
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup

# Streamlit UI Config
st.set_page_config(page_title="LinkedIn Sales Link Converter", layout="wide")
st.title(":link: LinkedIn Sales Navigator Link Converter")

# User Login Inputs
st.subheader(":key: Please enter your LinkedIn credentials")

email = st.text_input(":e-mail: Email:", placeholder="Enter your LinkedIn email")
password = st.text_input(":lock: Password:", type="password", placeholder="Enter your password", help="Your password is not stored.")

# File Upload Section
uploaded_file = st.file_uploader(":open_file_folder: Upload CSV with Sales Navigator Links (2nd Column)", type=["csv"])

# Function to log in to LinkedIn using requests
def login_to_linkedin(email, password):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    login_url = "https://www.linkedin.com/login"
    response = session.get(login_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find CSRF token
    csrf_token = soup.find("input", {"name": "loginCsrfParam"})
    if csrf_token:
        csrf_token = csrf_token["value"]
    else:
        return None  # Failed to get CSRF token

    # Submit login form
    login_payload = {
        "session_key": email,
        "session_password": password,
        "loginCsrfParam": csrf_token
    }

    login_response = session.post(login_url, data=login_payload, headers=headers)

    # Check if login was successful
    if "feed" in login_response.url or "checkpoints" in login_response.url:
        return session  # Return authenticated session
    else:
        return None  # Login failed

# Function to extract the final LinkedIn profile URL
def get_linkedin_redirect(session, sales_navigator_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        response = session.get(sales_navigator_url, headers=headers, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            return response.url  # Extract the final LinkedIn Profile URL
        else:
            return "Error: Unable to retrieve"
    except Exception as e:
        return "Error"

# Process file if uploaded
if uploaded_file and email and password:
    df = pd.read_csv(uploaded_file)

    if df.shape[1] < 2:
        st.error(":warning: The uploaded CSV must have at least two columns!")
    else:
        st.success(":white_check_mark: File uploaded successfully!")

        # Extract Sales Navigator Links (Assumed to be in the 2nd column)
        sales_links = df.iloc[:, 1].dropna().tolist()  # Drop empty rows and convert to list

        if not sales_links:
            st.error(":warning: No valid Sales Navigator links found in the file.")
        else:
            st.info(":arrows_counterclockwise: Logging into LinkedIn...")
            session = login_to_linkedin(email, password)

            if session:
                st.success(":white_check_mark: Successfully logged in!")
                st.info(":arrows_counterclockwise: Converting links... Please wait.")

                converted_links = []

                for index, link in enumerate(sales_links):
                    if "linkedin.com" in str(link):
                        converted_link = get_linkedin_redirect(session, link)
                        converted_links.append(converted_link)
                        st.write(f":white_check_mark: {index+1}/{len(sales_links)}: {converted_link}")

                        # :clock3: Delay to prevent LinkedIn from blocking requests
                        time.sleep(5)

                # Save converted links to a new CSV file
                df_filtered = df[df.iloc[:, 1].notna()].copy()  # Keep only rows with valid links
                df_filtered["Converted LinkedIn Links"] = converted_links  # Add new column

                output_csv = "converted_linkedin_links.csv"
                df_filtered.to_csv(output_csv, index=False)

                # Download button for final CSV
                with open(output_csv, "rb") as f:
                    st.download_button(":inbox_tray: Download Cleaned CSV", f, file_name=output_csv, mime="text/csv", key="download-csv")

                st.success(":white_check_mark: Conversion process completed!")
            else:
                st.error(":x: Login failed. Please check your email and password.")