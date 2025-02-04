import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Streamlit UI Config
st.set_page_config(page_title="LinkedIn Sales Link Converter", layout="wide")
st.title("🔗 LinkedIn Sales Navigator Link Converter")

# User Login Inputs
st.subheader("🔑 Please enter your LinkedIn credentials")
email = st.text_input("📧 Email:", placeholder="Enter your LinkedIn email")
password = st.text_input("🔒 Password:", type="password", placeholder="Enter your password", help="Your password is not stored.")

# File Upload Section
uploaded_file = st.file_uploader("📂 Upload CSV with Sales Navigator Links (2nd Column)", type=["csv"])

# Function to configure remote Selenium WebDriver
def get_driver():
    browserless_api_key = RiJiICITUmxNemad562a7bc35fd545275876ab991d  # Replace with your API Key
    selenium_url = f"https://chrome.browserless.io/webdriver?token={browserless_api_key}"

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode (no UI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Remote(command_executor=selenium_url, options=chrome_options)
    return driver

# Function to log into LinkedIn
def linkedin_login(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)  # Wait for the login page to load

    try:
        email_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")

        email_field.send_keys(email)
        password_field.send_keys(password)
        login_button.click()

        time.sleep(5)  # Allow time for login to complete

        if "feed" in driver.current_url:
            st.success("✅ Successfully logged into LinkedIn!")
            return True
        else:
            st.error("❌ Login failed! Please check your credentials.")
            return False
    except Exception as e:
        st.error(f"⚠️ Error logging in: {e}")
        return False

# Function to extract the final LinkedIn profile URL
def get_linkedin_redirect(driver, sales_navigator_url):
    try:
        driver.get(sales_navigator_url)
        time.sleep(5)  # Wait for redirection

        return driver.current_url  # Extract the final LinkedIn Profile URL
    except Exception as e:
        return "Error"

# Process file if uploaded
if uploaded_file and email and password:
    df = pd.read_csv(uploaded_file)

    if df.shape[1] < 2:
        st.error("⚠️ The uploaded CSV must have at least two columns!")
    else:
        st.success("✅ File uploaded successfully!")

        # Extract Sales Navigator Links (Assumed to be in the 2nd column)
        sales_links = df.iloc[:, 1].dropna().tolist()  # Drop empty rows and convert to list

        if not sales_links:
            st.error("⚠️ No valid Sales Navigator links found in the file.")
        else:
            st.info("🔄 Launching cloud browser...")
            driver = get_driver()

            if linkedin_login(driver, email, password):
                st.info("🔄 Converting links... Please wait.")

                converted_links = []

                for index, link in enumerate(sales_links):
                    if "linkedin.com" in str(link):
                        converted_link = get_linkedin_redirect(driver, link)
                        converted_links.append(converted_link)
                        st.write(f"✅ {index+1}/{len(sales_links)}: {converted_link}")

                        # 🕒 Delay to prevent LinkedIn from blocking requests
                        time.sleep(5)

                # Close browser after processing all links
                driver.quit()

                # Save converted links to a new CSV file
                df_filtered = df[df.iloc[:, 1].notna()].copy()  # Keep only rows with valid links
                df_filtered["Converted LinkedIn Links"] = converted_links  # Add new column

                output_csv = "converted_linkedin_links.csv"
                df_filtered.to_csv(output_csv, index=False)

                # Download button for final CSV
                with open(output_csv, "rb") as f:
                    st.download_button("📥 Download Cleaned CSV", f, file_name=output_csv, mime="text/csv", key="download-csv")

                st.success("✅ Conversion process completed!")

