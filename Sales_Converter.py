import streamlit as st
import pandas as pd
import requests
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

# Function to extract the final LinkedIn profile URL
def get_linkedin_redirect(sales_navigator_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(sales_navigator_url, headers=headers, allow_redirects=True, timeout=10)
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
            st.info(":arrows_counterclockwise: Converting links... Please wait.")

            converted_links = []

            for index, link in enumerate(sales_links):
                if "linkedin.com" in str(link):
                    converted_link = get_linkedin_redirect(link)
                    converted_links.append(converted_link)
                    st.write(f":white_check_mark: {index+1}/{len(sales_links)}: {converted_link}")

            # Save converted links to a new CSV file
            df_filtered = df[df.iloc[:, 1].notna()].copy()  # Keep only rows with valid links
            df_filtered["Converted LinkedIn Links"] = converted_links  # Add new column

            output_csv = "converted_linkedin_links.csv"
            df_filtered.to_csv(output_csv, index=False)

            # Download button for final CSV
            with open(output_csv, "rb") as f:
                st.download_button(":inbox_tray: Download Cleaned CSV", f, file_name=output_csv, mime="text/csv", key="download-csv")

            st.success(":white_check_mark: Conversion process completed!")