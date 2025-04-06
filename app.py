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
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "dict_loaded" not in st.session_state:
    st.session_state.dict_loaded = False

# Display previous chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# Creating columns for file uploaders
col1, col2 = st.columns(2)

# Upload CSV for analysis
with col1:
    st.subheader("Upload Transaction Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], key="transaction")
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.session_state.data_loaded = True
            st.success("Transaction data successfully uploaded and read.")
            st.write("### Transaction Data Preview")
            st.dataframe(st.session_state.uploaded_data.head())
        except Exception as e:
            st.error(f"Failed to load CSV file: {e}")

# Upload Data Dictionary
with col2:
    st.subheader("Upload Data Dictionary")
    data_dict_file = st.file_uploader("Choose a Data Dictionary file (CSV or TXT)", type=["csv", "txt"], key="dictionary")
    if data_dict_file is not None:
        try:
            if data_dict_file.name.endswith(".csv"):
                df_dict = pd.read_csv(data_dict_file)
                st.session_state.data_dict_text = df_dict.to_string()
            else:
                st.session_state.data_dict_text = data_dict_file.read().decode("utf-8")
            st.session_state.dict_loaded = True
            st.success("Data Dictionary loaded successfully.")
            st.write("### Data Dictionary Preview")
            if data_dict_file.name.endswith(".csv"):
                st.dataframe(df_dict.head())
            else:
                st.text_area("Dictionary Content", st.session_state.data_dict_text, height=150)
        except Exception as e:
            st.error(f"Failed to load Data Dictionary: {e}")

# Check if both files are loaded
if st.session_state.data_loaded and st.session_state.dict_loaded:
    st.success("Both transaction data and data dictionary are loaded! You can now analyze the data.")
else:
    if not st.session_state.data_loaded and not st.session_state.dict_loaded:
        st.warning("Please upload both transaction data and data dictionary.")
    elif not st.session_state.data_loaded:
        st.warning("Please upload transaction data.")
    else:
        st.warning("Please upload data dictionary.")

# Checkbox to trigger analysis
analyze_data_checkbox = st.checkbox("Analyze Data with AI", value=True)

# User input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)
    
    if model:
        try:
            if st.session_state.data_loaded and st.session_state.dict_loaded and analyze_data_checkbox:
                # Create a well-structured prompt that connects the dictionary to the transaction data
                data_columns = ", ".join(st.session_state.uploaded_data.columns.tolist())
                data_sample = st.session_state.uploaded_data.head(5).to_string()
                data_stats = st.session_state.uploaded_data.describe().to_string()
                
                prompt = f"""
I need you to analyze transaction data using the data dictionary provided.

DATA DICTIONARY:
{st.session_state.data_dict_text}

TRANSACTION DATA COLUMNS:
{data_columns}

TRANSACTION DATA SAMPLE (First 5 rows):
{data_sample}

TRANSACTION DATA STATISTICS:
{data_stats}

USER QUERY:
{user_input}

Instructions:
1. Use the data dictionary to understand what each column in the transaction data means
2. Reference the dictionary definitions when explaining results
3. Provide clear explanations of any insights or patterns
4. If the user's query requires specific analysis of certain columns, focus on those
5. Thai language responses are acceptable - respond in the same language as the user's query
"""
                response = model.generate_content(prompt)
                bot_response = response.text
            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please select the 'Analyze Data with AI' checkbox to enable analysis."
            elif not st.session_state.data_loaded:
                bot_response = "Please upload transaction data first."
            elif not st.session_state.dict_loaded:
                bot_response = "Please upload a data dictionary to help me understand the transaction data."
            else:
                # Just a regular chat without data analysis
                response = model.generate_content(user_input)
                bot_response = response.text
                
            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
            st.error(str(e))
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

# Add a section to display data dictionary information
if st.session_state.dict_loaded:
    with st.expander("Data Dictionary Reference"):
        st.write("Use this reference to understand the transaction data columns:")
        if data_dict_file.name.endswith(".csv"):
            st.dataframe(df_dict)
        else:
            st.text(st.session_state.data_dict_text)
