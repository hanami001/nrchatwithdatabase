import streamlit as st
import pandas as pd
import os
import google.generativeai as genai

# --- Page Config ---
st.set_page_config(page_title="Chat with CSV (Gemini)", layout="wide")
st.title("💬 Chat with Your CSV File (Gemini)")

# --- Configure Gemini API ---
try:
    key = st.secrets["gemini_api_key"]
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
except Exception as e:
    st.error("⚠️ Unable to load Gemini API key from secrets. Please check your configuration.")
    st.stop()

# --- Load Data Dictionary ---
@st.cache_data
def load_data_dictionary():
    path = os.path.join("files", "data_dictionary.csv")
    return pd.read_csv(path)

# --- Load Main CSV ---
@st.cache_data
def load_main_data():
    path = os.path.join("files", "your_data.csv")  # ← เปลี่ยนชื่อให้ตรงกับไฟล์จริง
    return pd.read_csv(path)

# --- Show Data Dictionary ---
st.subheader("📘 Data Dictionary")
try:
    dict_df = load_data_dictionary()
    st.dataframe(dict_df)
except FileNotFoundError:
    st.error("⚠️ data_dictionary.csv not found in /files")

# --- Show Main Data ---
st.subheader("📊 Main CSV Data")
try:
    df = load_main_data()
    st.dataframe(df.head(20))
except FileNotFoundError:
    st.error("⚠️ your_data.csv not found in /files")

# --- Chat Section ---
st.subheader("🧠 Ask Anything About the Data")

user_query = st.text_area("Type your question here")

if st.button("Ask"):
    if user_query and 'df' in locals():
        sample_data = df.head(5).to_csv(index=False)
        dict_text = dict_df.to_csv(index=False) if 'dict_df' in locals() else 'No data dictionary available.'

        prompt = f"""
You are a data assistant helping to analyze CSV data using pandas.

Here is a sample of the CSV:
{sample_data}

Here is the data dictionary:
{dict_text}

Now answer the following question using Python pandas code:
{user_query}
"""

        try:
            response = model.generate_content(prompt)
            st.code(response.text, language="python")
        except Exception as e:
            st.error(f"❌ Gemini Error: {str(e)}")
    else:
        st.warning("Please load data and enter a question.")
