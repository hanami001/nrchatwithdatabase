import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

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
        model = genai.GenerativeModel("gemini-pro")
        st.success("Gemini API Key successfully configured.")
    except Exception as e:
        st.error(f"An error occurred while setting up the Gemini model: {e}")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "transaction_data" not in st.session_state:
    st.session_state.transaction_data = None
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
    transaction_file = st.file_uploader("Choose a CSV file", type=["csv"], key="transaction_uploader")
    if transaction_file is not None:
        try:
            data = pd.read_csv(transaction_file)
            st.session_state.transaction_data = data
            st.success("Transaction data successfully uploaded and read.")
            st.write("### Transaction Data Preview")
            st.dataframe(data.head())
        except Exception as e:
            st.error(f"An error occurred while reading the transaction file: {e}")

# Upload Data Dictionary
with col2:
    st.subheader("Upload Data Dictionary")
    dictionary_file = st.file_uploader("Choose a dictionary file", type=["csv"], key="dictionary_uploader")
    if dictionary_file is not None:
        try:
            dict_data = pd.read_csv(dictionary_file)
            st.session_state.dictionary_data = dict_data
            st.success("Data dictionary successfully uploaded and read.")
            st.write("### Data Dictionary Preview")
            st.dataframe(dict_data.head())
        except Exception as e:
            st.error(f"An error occurred while reading the dictionary file: {e}")

# Checkbox to analyze data
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# Function to convert NumPy types to Python native types for JSON serialization
def convert_to_native_types(obj):
    import numpy as np
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(i) for i in obj]
    else:
        return obj

# Function to perform detailed data analysis
def analyze_data_for_question(question, transaction_data, dictionary_data=None):
    # Prepare data summary
    data_stats = {}
    
    # Basic statistics
    if 'date' in transaction_data.columns or 'Date' in transaction_data.columns:
        date_col = 'date' if 'date' in transaction_data.columns else 'Date'
        transaction_data[date_col] = pd.to_datetime(transaction_data[date_col], errors='coerce')
        
    # Get column summaries for numeric columns
    for col in transaction_data.select_dtypes(include=['number']).columns:
        data_stats[col] = {
            "sum": float(transaction_data[col].sum()),
            "mean": float(transaction_data[col].mean()),
            "max": float(transaction_data[col].max()),
            "min": float(transaction_data[col].min())
        }
    
    # Get basic info about categorical columns
    for col in transaction_data.select_dtypes(include=['object']).columns:
        # Convert value_counts to regular Python dict with native types
        top_values = transaction_data[col].value_counts().head(5).to_dict()
        top_values_native = {str(k): int(v) for k, v in top_values.items()}
        
        data_stats[col] = {
            "unique_values": int(transaction_data[col].nunique()),
            "top_values": top_values_native
        }
    
    # If there are date columns, get month-wise aggregations
    date_columns = transaction_data.select_dtypes(include=['datetime64']).columns
    if len(date_columns) > 0:
        for date_col in date_columns:
            transaction_data[f'month_{date_col}'] = transaction_data[date_col].dt.month
            transaction_data[f'year_{date_col}'] = transaction_data[date_col].dt.year
            
            # Add monthly aggregations if there's an amount/price column
            numeric_cols = transaction_data.select_dtypes(include=['number']).columns
            for num_col in numeric_cols:
                if 'amount' in num_col.lower() or 'price' in num_col.lower() or 'sale' in num_col.lower() or 'revenue' in num_col.lower():
                    monthly_data = transaction_data.groupby([f'year_{date_col}', f'month_{date_col}'])[num_col].sum().reset_index()
                    # Convert DataFrame to dict and ensure all values are native Python types
                    monthly_dict = []
                    for _, row in monthly_data.iterrows():
                        month_entry = {}
                        for col_name in monthly_data.columns:
                            value = row[col_name]
                            if isinstance(value, (pd.Timestamp, pd._libs.tslibs.timestamps.Timestamp)):
                                month_entry[col_name] = value.strftime('%Y-%m-%d')
                            else:
                                month_entry[col_name] = convert_to_native_types(value)
                        monthly_dict.append(month_entry)
                    
                    data_stats[f'monthly_{num_col}'] = monthly_dict
    
    # Make sure all values are JSON serializable
    return convert_to_native_types(data_stats)

# Capture input and generate response
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)
    
    if model:
        try:
            if st.session_state.transaction_data is not None and analyze_data_checkbox:
                # Perform data analysis
                detailed_analysis = analyze_data_for_question(
                    user_input, 
                    st.session_state.transaction_data,
                    st.session_state.dictionary_data
                )
                
                # Prepare data context
                transaction_info = f"Transaction Data Columns: {', '.join(st.session_state.transaction_data.columns.tolist())}\n"
                transaction_info += f"Number of records: {len(st.session_state.transaction_data)}\n\n"
                
                # Add dictionary context if available
                dictionary_info = ""
                if st.session_state.dictionary_data is not None:
                    dictionary_info = "Data Dictionary Information:\n"
                    for _, row in st.session_state.dictionary_data.iterrows():
                        # Assuming dictionary has field_name and description columns
                        field_cols = [col for col in st.session_state.dictionary_data.columns if 'field' in col.lower() or 'column' in col.lower()]
                        desc_cols = [col for col in st.session_state.dictionary_data.columns if 'desc' in col.lower() or 'mean' in col.lower()]
                        
                        if field_cols and desc_cols:
                            field = row[field_cols[0]]
                            description = row[desc_cols[0]]
                            dictionary_info += f"- {field}: {description}\n"
                
                # Generate AI response based on user input and data
                # Convert detailed analysis to safe string representation for prompt
                analysis_str = str(detailed_analysis)
                
                prompt = f"""
                User Question: {user_input}
                
                Transaction Data Information:
                {transaction_info}
                
                Dictionary Information:
                {dictionary_info}
                
                Detailed Analysis:
                {analysis_str}
                
                Please analyze the transaction data to answer the user's question.
                If you're referring to specific months like January 2025 (Jan 2025), use the monthly aggregation data if available.
                """
                
                response = model.generate_content(prompt)
                answer = response.text
                
                # Create a summarized explanation with customer persona insights
                explain_the_results = f'''
                The user asked: {user_input}
                Here is the result: {answer}
                
                Please answer the question directly and concisely based on the data provided.
                If the data shows regular patterns or specific preferences, include your opinions about the persona of this customer.
                Use data points to support any persona insights.
                If you cannot answer the question with the available data, explain specifically what data is missing.
                '''
                
                final_response = model.generate_content(explain_the_results)
                bot_response = final_response.text
                
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please select the 'Analyze CSV Data with AI' checkbox to enable analysis."
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif st.session_state.transaction_data is None:
                bot_response = "Please upload a transaction CSV file first, then ask me to analyze it."
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            else:
                response = model.generate_content(user_input)
                bot_response = response.text
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
            st.error(f"Error details: {type(e).__name__}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")
