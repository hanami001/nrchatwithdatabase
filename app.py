import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("🤖 My Chatbot and Data Analysis App")
st.subheader("Conversation and Data Analysis")

# Capture Gemini API Key
gemini_api_key = st.secrets['gemini_api_key']

# Initialize the Gemini Model
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini API Key successfully configured.")
    except Exception as e:
        st.error(f"An error occurred while setting up the Gemini model: {e}")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "data_dict_text" not in st.session_state:
    st.session_state.data_dict_text = ""

# Display previous chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# Upload CSV for analysis
st.subheader("Upload CSV for Analysis")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
if uploaded_file is not None:
    try:
        st.session_state.uploaded_data = pd.read_csv(uploaded_file)
        st.success("File successfully uploaded and read.")
        st.write("### Uploaded Data Preview")
        st.dataframe(st.session_state.uploaded_data.head())
    except Exception as e:
        st.error(f"Failed to load CSV file: {e}")

# Upload Data Dictionary
st.subheader("Upload Data Dictionary")
data_dict_file = st.file_uploader("Choose a Data Dictionary file (CSV or TXT)", type=["csv", "txt"])
if data_dict_file is not None:
    try:
        if data_dict_file.name.endswith(".csv"):
            df_dict = pd.read_csv(data_dict_file)
            st.session_state.data_dict_text = df_dict.to_string()
        else:
            st.session_state.data_dict_text = data_dict_file.read().decode("utf-8")
        st.success("Data Dictionary loaded successfully.")
    except Exception as e:
        st.error(f"Failed to load Data Dictionary: {e}")

# Checkbox to trigger analysis
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# User input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                if "analyze" in user_input.lower() or "insight" in user_input.lower():
                    data_description = st.session_state.uploaded_data.describe().to_string()
                    prompt = f"""Analyze the following dataset and provide insights.

Data Dictionary:
{st.session_state.data_dict_text}

Data Summary:
{data_description}
"""
                    response = model.generate_content(prompt)
                    bot_response = response.text
                else:
                    response = model.generate_content(user_input)
                    bot_response = response.text
            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please select the 'Analyze CSV Data with AI' checkbox to enable analysis."
            else:
                bot_response = "Please upload a CSV file first, then ask me to analyze it."

            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")
