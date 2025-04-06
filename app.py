import streamlit as st
import pandas as pd
import google.generativeai as genai
import textwrap

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

# Function to format Gemini responses similar to madt7204
def to_markdown(text):
    text = text.replace('•', ' *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# File uploader for CSV
df = None
df_name = "df"
data_dict_text = ""
example_record = ""

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df = df.apply(lambda col: pd.to_datetime(col) if col.name.lower().startswith("date") else col)
    st.session_state.uploaded_data = df
    st.dataframe(df)
    df_name = "df"
    data_dict_text = "\n".join([f"- {col}: {df[col].dtype}" for col in df.columns])
    example_record = df.head(2).to_markdown()

# Chat interaction
user_input = st.text_input("Ask something:")
if st.button("Send") and user_input:
    if model and df is not None:
        question = user_input
        prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.

Here's the context:

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. **Crucially, use the `exec()` function to execute the generated code.**
3. Do not import pandas
4. Change date column type to datetime
5. **Store the result of the executed code in a variable named `ANSWER`.**
   This variable should hold the answer to the user's question (e.g., a filtered DataFrame, a calculated value, etc.).
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`. Do not include code to load the DataFrame.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a single value), ensure the `query_result` variable holds that format.
"""

        response = model.generate_content(prompt)
        markdown_text = to_markdown(response.text)
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", markdown_text))
        try:
            local_vars = {df_name: df}
            exec(response.text, {}, local_vars)
            if "ANSWER" in local_vars:
                st.subheader("Query Result:")
                st.write(local_vars["ANSWER"])
        except Exception as e:
            st.error(f"Error while executing generated code: {e}")
    else:
        st.error("Gemini model or DataFrame is not initialized.")

# Display chat history
for role, message in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(message)
