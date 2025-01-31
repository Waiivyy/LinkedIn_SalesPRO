import streamlit as st
import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# Streamlit UI Config
st.set_page_config(page_title="LinkedIn Sales Link Converter", layout="wide")
st.title(":link: LinkedIn Sales Navigator Link Converter")

# User Login Inputs
st.subheader(":key: Please enter your LinkedIn credentials")

email = st.text_input(":e-mail: Email:", placeholder="Enter your LinkedIn email")
password = st.text_input(":lock: Password:", type="password", placeholder="Enter your password", help="Your password is not stored.")

# File Upload Section
uploaded_file = st.file_uploader(":open_file_folder: Upload CSV with Sales Navigator Links (2nd Column)", type=["csv"])

# Temporary storage for CSV download
converted_file_path = "converted_linkedin_links.csv"

# Function to initialize Selenium WebDriver
def get_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)  # Keep browser open
    chrome_options.add_argument("--start-maximized")  # Open browser maximized
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument("--headless")  # Run in headless mode (faster execution)
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    # Automatically download the correct ChromeDriver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)  # Set a maximum timeout of 30 seconds per page load
    return driver

# Function to log into LinkedIn
def linkedin_login(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)  # Wait for page to load

    try:
        email_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")

        email_field.send_keys(email)
        password_field.send_keys(password)
        login_button.click()

        time.sleep(5)  # Allow time for login to complete

        # Check if login was successful
        if "feed" in driver.current_url:
            st.success(":white_check_mark: Successfully logged into LinkedIn!")
            return True
        else:
            st.error(":x: Login failed! Please check your credentials.")
            return False
    except Exception as e:
        st.error(f":warning: Error logging in: {e}")
        return False

# Function to process Sales Navigator links
def process_links(driver, sales_links):
    converted_links = []

    for index, link in enumerate(sales_links):
        if "linkedin.com" in str(link):
            retries = 3  # Retry logic: Try each link up to 3 times
            while retries > 0:
                try:
                    driver.get(link)
                    time.sleep(4)  # Wait for page to load

                    # Get redirected LinkedIn profile URL
                    converted_link = driver.current_url
                    converted_links.append(converted_link)
                    st.write(f":white_check_mark: {index+1}/{len(sales_links)}: {converted_link}")
                    break  # Exit retry loop if successful

                except (TimeoutException, WebDriverException) as e:
                    retries -= 1
                    if retries == 0:
                        st.error(f":warning: Skipping link {index+1} due to repeated timeouts.")
                        converted_links.append("Error")
                    else:
                        st.warning(f":arrows_counterclockwise: Retrying link {index+1} ({3 - retries}/3 attempts)")
                        time.sleep(5)  # Wait before retrying

    return converted_links

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
            # Initialize WebDriver and log in
            driver = get_driver()
            if linkedin_login(driver, email, password):
                # Process links with retry logic
                converted_links = process_links(driver, sales_links)

                # Close browser after processing all links
                driver.quit()

                # Save converted links to a new CSV file
                df_filtered = df[df.iloc[:, 1].notna()].copy()  # Keep only rows with valid links
                df_filtered["Converted LinkedIn Links"] = converted_links  # Add new column

                df_filtered.to_csv(converted_file_path, index=False)
                st.success(":white_check_mark: Conversion process completed!")

# Prevent Streamlit from rerunning when clicking the download button
if os.path.exists(converted_file_path):
    with open(converted_file_path, "rb") as f:
        st.download_button(":inbox_tray: Download Cleaned CSV", f, file_name=converted_file_path, mime="text/csv", key="download-csv")