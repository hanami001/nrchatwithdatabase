import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("! My Chatbot and Data Analysis App")
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
if "dictionary_data" not in st.session_state:
    st.session_state.dictionary_data = None

# Display chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# Create two columns for file uploaders
col1, col2 = st.columns(2)

# Upload CSV for analysis
with col1:
    st.subheader("Upload Transaction Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], key="transaction_data")
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("Transaction data successfully uploaded and read.")
            st.write("### Transaction Data Preview")
            st.dataframe(st.session_state.uploaded_data.head())
        except Exception as e:
            st.error(f"An error occurred while reading the transaction file: {e}")

# Upload Data Dictionary
with col2:
    st.subheader("Upload Data Dictionary")
    dictionary_file = st.file_uploader("Choose a dictionary file", type=["csv"], key="dict_file_uploader")
    if dictionary_file is not None:
        try:
            st.session_state.dictionary_data = pd.read_csv(dictionary_file)
            st.success("Data dictionary successfully uploaded and read.")
            st.write("### Data Dictionary Preview")
            st.dataframe(st.session_state.dictionary_data.head())
        except Exception as e:
            st.error(f"An error occurred while reading the dictionary file: {e}")

# Checkbox to analyze data
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# Capture input and generate response
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)
    
    if model:
        try:
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                # Prepare data context with both transaction data and dictionary if available
                data_context = "Transaction Data:\n"
                data_context += st.session_state.uploaded_data.describe().to_string()
                
                # Add dictionary context if available
                if st.session_state.dictionary_data is not None:
                    data_context += "\n\nData Dictionary:\n"
                    data_context += st.session_state.dictionary_data.to_string()
                
                # Generate AI response based on user input and data
                prompt = f"""
                User Question: {user_input}
                
                Data Context:
                {data_context}
                
                Please analyze the transaction data considering the data dictionary definitions.
                """
                
                response = model.generate_content(prompt)
                answer = response.text
                
                # Create a summarized explanation with customer persona insights
                explain_the_results = f'''
                The user asked: {user_input}
                Here is the result: {answer}
                
                Please answer the question and summarize the answer concisely.
                Include your opinions about the persona of this customer based on the transaction data.
                '''
                
                final_response = model.generate_content(explain_the_results)
                bot_response = final_response.text
                
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please select the 'Analyze CSV Data with AI' checkbox to enable analysis."
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif st.session_state.uploaded_data is None:
                bot_response = "Please upload a transaction CSV file first, then ask me to analyze it."
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif st.session_state.dictionary_data is None:
                bot_response = "Transaction data uploaded, but data dictionary is missing. For best results, please upload both files."
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")
