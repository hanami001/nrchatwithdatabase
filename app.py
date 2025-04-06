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
if "columns_explained" not in st.session_state:
    st.session_state.columns_explained = False
if "user_persona" not in st.session_state:
    st.session_state.user_persona = {}

# Display previous chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# File upload section with columns for better layout
col1, col2 = st.columns(2)

# Upload CSV for analysis in the first column
with col1:
    st.subheader("Upload Transaction Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], key="transaction_data")
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("Transaction data successfully uploaded.")
            st.write("### Transaction Data Preview")
            st.dataframe(st.session_state.uploaded_data.head())
        except Exception as e:
            st.error(f"Failed to load transaction data: {e}")

# Upload Data Dictionary in the second column
with col2:
    st.subheader("Upload Data Dictionary")
    data_dict_file = st.file_uploader("Choose a Data Dictionary file (CSV or TXT)", type=["csv", "txt"], key="data_dict")
    if data_dict_file is not None:
        try:
            if data_dict_file.name.endswith(".csv"):
                df_dict = pd.read_csv(data_dict_file)
                st.session_state.data_dict_text = df_dict.to_string()
                # Display preview of the data dictionary
                st.success("Data Dictionary loaded successfully.")
                st.write("### Data Dictionary Preview")
                st.dataframe(df_dict.head())
            else:
                content = data_dict_file.read().decode("utf-8")
                st.session_state.data_dict_text = content
                st.success("Data Dictionary loaded successfully.")
                st.write("### Data Dictionary Preview")
                st.text(content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            st.error(f"Failed to load Data Dictionary: {e}")

# Status indicators and controls
status_col1, status_col2 = st.columns(2)
with status_col1:
    has_transaction = st.session_state.uploaded_data is not None
    has_dictionary = st.session_state.data_dict_text != ""
    st.info(f"Transaction Data: {'✅ Loaded' if has_transaction else '❌ Not Loaded'}")
    st.info(f"Data Dictionary: {'✅ Loaded' if has_dictionary else '❌ Not Loaded'}")

with status_col2:
    # Checkbox to trigger analysis
    analyze_data_checkbox = st.checkbox("Analyze Data with AI", value=True)
    # Checkbox to always include dictionary context
    always_use_dict = st.checkbox("Always Include Dictionary Context", value=True, 
                                help="Always include data dictionary context in every query")
    # Response length control
    response_length = st.select_slider(
        "Response Length",
        options=["Very Brief", "Brief", "Moderate", "Detailed", "Comprehensive"],
        value="Moderate",
        help="Control how detailed the AI responses should be"
    )
    # Add persona analysis option
    include_persona = st.checkbox("Include Customer Persona Analysis", value=True,
                                help="Include analysis of customer behavior and characteristics")

# User input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)
    
    if model:
        try:
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                # Get data summary
                data_description = st.session_state.uploaded_data.describe().to_string()
                data_columns = ", ".join(st.session_state.uploaded_data.columns.tolist())
                
                # Prepare context from data dictionary
                dict_context = ""
                if st.session_state.data_dict_text:
                    dict_context = f"""
Data Dictionary Information:
{st.session_state.data_dict_text}

The data dictionary above explains the meaning of each column in the transaction data.
When answering questions about the transaction data, please refer to this dictionary to understand what each column represents.
"""
                
                # Response length instructions
                length_instructions = {
                    "Very Brief": "Provide an extremely concise answer in 1-2 sentences maximum. Focus only on the key facts.",
                    "Brief": "Keep your response short and to the point, using no more than 3-4 sentences.",
                    "Moderate": "Provide a balanced answer with sufficient detail but avoid being overly verbose.",
                    "Detailed": "Include comprehensive details and explanations in your answer.",
                    "Comprehensive": "Provide an in-depth analysis with all relevant details and supporting information."
                }
                
                # Create a comprehensive prompt that includes the data dictionary context and response length control
                prompt = f"""
I have a question about my transaction data: {user_input}

Transaction Data Information:
- Columns in the dataset: {data_columns}
- Data summary statistics: 
{data_description}

{dict_context if st.session_state.data_dict_text and (always_use_dict or "dictionary" in user_input.lower() or "explain" in user_input.lower() or "what is" in user_input.lower()) else ""}

Response Instructions:
{length_instructions[response_length]}

Please analyze the transaction data to answer my question. If my question refers to specific columns or terms, use the data dictionary to understand what they mean.
"""
                # Get initial response from Gemini
                response = model.generate_content(prompt)
                initial_answer = response.text
                
                # Generate customer persona if enabled
                if include_persona and st.session_state.uploaded_data is not None:
                    # Update the prompt to include persona analysis
                    explain_prompt = f"""
The user asked: {user_input}

Here is the analysis result: {initial_answer}

Based on the user's question and the transaction data, provide:
1. A {response_length.lower()} answer to the user's question
2. A brief summary of the key insights
3. Your analysis of the customer persona based on the transaction patterns

For the persona analysis, consider spending habits, transaction frequency, average transaction values, and any other insights you can glean from the data.
"""
                    # Get enhanced response with persona
                    enhanced_response = model.generate_content(explain_prompt)
                    bot_response = enhanced_response.text
                else:
                    bot_response = initial_answer
                    
            elif not analyze_data_checkbox:
                bot_response = "Data analysis is disabled. Please select the 'Analyze Data with AI' checkbox to enable analysis."
            else:
                bot_response = "Please upload both transaction data and data dictionary files first, then ask me to analyze them."
            
            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
    else:
        st.warning("Please configure the Gemini API Key to enable chat responses.")

# Add explanation of how to use the app
with st.expander("How to use this app"):
    st.markdown("""
    1. **Upload your transaction data** (CSV file)
    2. **Upload your data dictionary** (CSV or TXT file that explains each column in your transaction data)
    3. **Set your preferences**:
       - Choose response length
       - Enable/disable persona analysis
       - Control dictionary context inclusion
    4. **Ask questions** about your transaction data
    5. The AI will use the data dictionary to understand column meanings when analyzing your data
    
    **Example questions you can ask:**
    - Show me a summary of the transaction data
    - What is the average value of [column name]?
    - Can you explain what the column [column name] means?
    - Find transactions with the highest values
    - Analyze spending patterns in the data
    - What does my transaction history say about me as a customer?
    """)
