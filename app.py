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
    st.error("⚠️ Unable to load Gemini API key from secrets.")
    st.stop()

# --- Ensure 'files/' folder exists ---
os.makedirs("files", exist_ok=True)

# --- Upload Section ---
st.subheader("📂 Upload Your CSV Files")

with st.form("upload_form"):
    data_dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type="csv", key="dict")
    data_file = st.file_uploader("📊 Upload Main Data CSV", type="csv", key="data")
    submitted = st.form_submit_button("Load Files")

# --- After Upload ---
if submitted:
    if data_dict_file is not None and data_file is not None:
        # Save uploaded files to 'files/' folder
        dict_path = os.path.join("files", "data_dictionary.csv")
        data_path = os.path.join("files", "your_data.csv")

        with open(dict_path, "wb") as f:
            f.write(data_dict_file.read())

        with open(data_path, "wb") as f:
            f.write(data_file.read())

        # Load CSV files
        try:
            dict_df = pd.read_csv(dict_path)
            df = pd.read_csv(data_path)
        except Exception as e:
            st.error(f"❌ Error loading CSV files: {str(e)}")
            st.stop()

        st.success("✅ Files uploaded and saved successfully!")

        # --- Show Data Dictionary ---
        st.subheader("📘 Data Dictionary")
        st.dataframe(dict_df)

        # --- Show Sample of Main Data ---
        st.subheader("📊 Preview of Main Data")
        st.dataframe(df.head(20))

        # --- Chat Section ---
        st.subheader("🧠 Ask Anything About the Data")
        user_query = st.text_area("Type your question here")

        if st.button("Ask"):
            if user_query:
                sample_data = df.head(5).to_csv(index=False)
                dict_text = dict_df.to_csv(index=False)

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
                st.warning("Please enter a question.")
    else:
        st.warning("📌 Please upload both Data Dictionary and Main Data files before proceeding.")
