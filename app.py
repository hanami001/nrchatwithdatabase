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
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
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
if "column_descriptions" not in st.session_state:
    st.session_state.column_descriptions = {}
if "dictionary_formatted_text" not in st.session_state:
    st.session_state.dictionary_formatted_text = ""
if "show_file_uploaders" not in st.session_state:
    st.session_state.show_file_uploaders = False

# Display chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# Add a toggle button for showing/hiding file uploaders
if st.button("Toggle File Upload Section", key="toggle_file_upload"):
    st.session_state.show_file_uploaders = not st.session_state.show_file_uploaders

# Only show the file upload section if toggle is on
if st.session_state.show_file_uploaders:
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
                
                # Process dictionary into a more usable format
                st.session_state.column_descriptions, st.session_state.dictionary_formatted_text = process_data_dictionary(dict_data)
            except Exception as e:
                st.error(f"An error occurred while reading the dictionary file: {e}")

    # Checkbox to analyze data
    analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")
else:
    # If file uploaders are hidden, we still need the checkbox state for data analysis
    analyze_data_checkbox = st.session_state.get("analyze_data_checkbox", False)

# Function to process the data dictionary into a usable format
def process_data_dictionary(dict_data):
    column_descriptions = {}
    formatted_text = ""
    
    # First, print the actual column names from the dictionary file for debugging
    actual_columns = dict_data.columns.tolist()
    print(f"Actual dictionary columns: {actual_columns}")
    
    # Try to intelligently identify which columns contain what information
    # based on column names and content patterns
    
    # Identify column name column
    name_cols = [col for col in actual_columns if any(term in col.lower() for term in 
                ['field', 'column', 'variable', 'name', 'attribute', 'feature'])]
    
    # Identify data type column
    type_cols = [col for col in actual_columns if any(term in col.lower() for term in 
                ['type', 'datatype', 'data_type', 'format', 'dtype'])]
    
    # Identify description column
    desc_cols = [col for col in actual_columns if any(term in col.lower() for term in 
                ['desc', 'definition', 'meaning', 'explanation', 'info', 'comment', 'documentation'])]
    
    # If common naming patterns weren't found, try to identify columns by content analysis
    if not name_cols and len(actual_columns) >= 1:
        # Check first few rows to see if any column looks like it contains field names
        # Field names typically have no spaces and follow naming conventions
        for col in actual_columns:
            sample_values = dict_data[col].head(5).astype(str)
            # Check if values look like field names (no spaces, consistent format)
            if all(not ' ' in val for val in sample_values if not pd.isna(val)):
                name_cols.append(col)
                break
    
    if not type_cols and len(actual_columns) >= 2:
        # Data types are usually short strings like "int", "varchar", "text", etc.
        for col in actual_columns:
            if col in name_cols:
                continue
            sample_values = dict_data[col].head(5).astype(str)
            # Check if values look like data types (short, consistent format)
            if all(len(val) < 20 for val in sample_values if not pd.isna(val)):
                type_cols.append(col)
                break
    
    if not desc_cols and len(actual_columns) >= 3:
        # Descriptions are usually longer text
        for col in actual_columns:
            if col in name_cols or col in type_cols:
                continue
            sample_values = dict_data[col].head(5).astype(str)
            # Check if values look like descriptions (longer text)
            if any(len(val) > 20 for val in sample_values if not pd.isna(val)):
                desc_cols.append(col)
                break
    
    # Default to positional fallbacks if we still couldn't identify columns
    if not name_cols and len(actual_columns) >= 1:
        name_cols = [actual_columns[0]]
    
    if not type_cols and len(actual_columns) >= 2:
        type_cols = [actual_columns[1]]
    
    if not desc_cols and len(actual_columns) >= 3:
        desc_cols = [actual_columns[2]]
    
    # Print what we identified for debugging
    print(f"Identified name column: {name_cols[0] if name_cols else 'None'}")
    print(f"Identified type column: {type_cols[0] if type_cols else 'None'}")
    print(f"Identified description column: {desc_cols[0] if desc_cols else 'None'}")
    
    # Use the identified columns
    name_col = name_cols[0] if name_cols else None
    type_col = type_cols[0] if type_cols else None
    desc_col = desc_cols[0] if desc_cols else None
    
    # Create a dictionary mapping field names to descriptions
    if name_col:
        for _, row in dict_data.iterrows():
            field_name = str(row[name_col]).strip()
            
            # Skip empty field names
            if not field_name or pd.isna(field_name):
                continue
            
            # Get data type (if available)
            data_type = ""
            if type_col:
                data_type = str(row[type_col]).strip() if not pd.isna(row[type_col]) else ""
            
            # Get description
            description = ""
            if desc_col:
                description = str(row[desc_col]).strip() if not pd.isna(row[desc_col]) else ""
            
            # Store in dictionary
            column_descriptions[field_name] = {
                'data_type': data_type,
                'description': description
            }
    
    # Create formatted text as requested
    formatted_lines = []
    for field_name, details in column_descriptions.items():
        data_type = details['data_type']
        description = details['description']
        
        line = f"- {field_name}"
        if data_type:
            line += f": {data_type}"
        if description:
            if data_type:
                line += f". {description}"
            else:
                line += f": {description}"
        
        formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    
    return column_descriptions, formatted_text

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
    
    # Process all columns, not just a subset
    all_columns = transaction_data.columns.tolist()
    data_stats["all_columns"] = all_columns
    data_stats["row_count"] = len(transaction_data)
    
    # Basic column type information
    data_stats["column_types"] = {col: str(transaction_data[col].dtype) for col in all_columns}
    
    # Identify and process date columns
    date_columns = []
    for col in all_columns:
        # Check if column name suggests a date
        if any(date_term in col.lower() for date_term in ['date', 'time', 'day', 'month', 'year']):
            try:
                transaction_data[col] = pd.to_datetime(transaction_data[col], errors='coerce')
                date_columns.append(col)
                data_stats[f"{col}_is_date"] = True
            except:
                pass
    
    # Explicitly detect date columns by trying to convert them
    for col in transaction_data.select_dtypes(include=['object']).columns:
        if col not in date_columns:
            # Try to convert to datetime
            try:
                temp_series = pd.to_datetime(transaction_data[col], errors='coerce')
                # If >50% of values converted successfully, consider it a date
                if temp_series.notna().sum() > len(transaction_data) * 0.5:
                    transaction_data[col] = temp_series
                    date_columns.append(col)
                    data_stats[f"{col}_is_date"] = True
            except:
                pass
    
    # Get column summaries for numeric columns
    for col in transaction_data.select_dtypes(include=['number']).columns:
        data_stats[col] = {
            "sum": float(transaction_data[col].sum()),
            "mean": float(transaction_data[col].mean()),
            "median": float(transaction_data[col].median()),
            "max": float(transaction_data[col].max()),
            "min": float(transaction_data[col].min()),
            "std": float(transaction_data[col].std()),
            "null_count": int(transaction_data[col].isna().sum()),
            "null_percentage": float(transaction_data[col].isna().mean() * 100)
        }
    
    # Get basic info about categorical columns
    for col in transaction_data.select_dtypes(include=['object', 'category']).columns:
        if col not in date_columns:
            # Convert value_counts to regular Python dict with native types
            value_counts = transaction_data[col].value_counts()
            top_values = value_counts.head(10).to_dict()
            top_values_native = {str(k): int(v) for k, v in top_values.items()}
            
            data_stats[col] = {
                "unique_values": int(transaction_data[col].nunique()),
                "top_values": top_values_native,
                "null_count": int(transaction_data[col].isna().sum()),
                "null_percentage": float(transaction_data[col].isna().mean() * 100)
            }
            
            # For columns with few unique values (<20), include percentage distribution
            if transaction_data[col].nunique() < 20:
                percentage_dict = (value_counts / len(transaction_data) * 100).to_dict()
                data_stats[col]["value_percentages"] = {str(k): float(v) for k, v in percentage_dict.items()}
    
    # Process date columns
    for date_col in date_columns:
        if transaction_data[date_col].notna().any():
            # Basic date statistics
            data_stats[date_col] = {
                "min_date": transaction_data[date_col].min().strftime('%Y-%m-%d'),
                "max_date": transaction_data[date_col].max().strftime('%Y-%m-%d'),
                "null_count": int(transaction_data[date_col].isna().sum()),
                "null_percentage": float(transaction_data[date_col].isna().mean() * 100)
            }
            
            # Extract time components
            transaction_data[f'year_{date_col}'] = transaction_data[date_col].dt.year
            transaction_data[f'month_{date_col}'] = transaction_data[date_col].dt.month
            transaction_data[f'day_{date_col}'] = transaction_data[date_col].dt.day
            
            # Create month-year string for readable grouping
            transaction_data[f'month_year_{date_col}'] = transaction_data[date_col].dt.strftime('%Y-%m')
            
            # Monthly distribution
            monthly_counts = transaction_data[f'month_year_{date_col}'].value_counts().sort_index().to_dict()
            data_stats[f"{date_col}_monthly_distribution"] = {str(k): int(v) for k, v in monthly_counts.items()}
            
            # Find numeric columns that might represent values to aggregate
            numeric_cols = transaction_data.select_dtypes(include=['number']).columns
            value_cols = [col for col in numeric_cols if any(term in col.lower() for term in 
                         ['amount', 'price', 'revenue', 'sales', 'cost', 'profit', 'qty', 'quantity', 'value'])]
            
            # If no obvious value columns, use all numeric columns
            if not value_cols:
                value_cols = numeric_cols
            
            # For each value column, create monthly aggregations
            for value_col in value_cols:
                # Monthly aggregation by sum
                monthly_agg = transaction_data.groupby(f'month_year_{date_col}')[value_col].agg(['sum', 'mean', 'count']).reset_index()
                monthly_agg.columns = [f'month_year_{date_col}', f'sum_{value_col}', f'avg_{value_col}', f'count_{value_col}']
                
                # Convert to list of dictionaries for easier JSON conversion
                monthly_data = []
                for _, row in monthly_agg.iterrows():
                    entry = {}
                    for col_name in monthly_agg.columns:
                        entry[col_name] = convert_to_native_types(row[col_name])
                    monthly_data.append(entry)
                
                data_stats[f"monthly_{date_col}_{value_col}"] = monthly_data
    
            # Look for potential category columns to do cross analysis
            categorical_cols = [col for col in transaction_data.select_dtypes(include=['object', 'category']).columns 
                               if col not in date_columns and transaction_data[col].nunique() < 20]
            
            # For each categorical column, create aggregations
            for cat_col in categorical_cols:
                # For each value column, aggregate by category
                for value_col in value_cols:
                    category_agg = transaction_data.groupby(cat_col)[value_col].agg(['sum', 'mean', 'count']).reset_index()
                    category_agg.columns = [cat_col, f'sum_{value_col}', f'avg_{value_col}', f'count_{value_col}']
                    
                    # Convert to list of dictionaries for easier JSON conversion
                    category_data = []
                    for _, row in category_agg.iterrows():
                        entry = {}
                        for col_name in category_agg.columns:
                            entry[col_name] = convert_to_native_types(row[col_name])
                        category_data.append(entry)
                    
                    data_stats[f"{cat_col}_{value_col}_analysis"] = category_data
    
    # Add correlation matrix for numeric columns
    if len(transaction_data.select_dtypes(include=['number']).columns) > 1:
        corr_matrix = transaction_data.select_dtypes(include=['number']).corr().round(2)
        corr_data = {}
        for col1 in corr_matrix.columns:
            corr_data[col1] = {}
            for col2 in corr_matrix.columns:
                corr_data[col1][col2] = float(corr_matrix.loc[col1, col2])
        data_stats["correlation_matrix"] = corr_data
    
    # Make sure all values are JSON serializable
    return convert_to_native_types(data_stats)

# Capture input and generate response
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)
    
    # Save the state of the analyze checkbox
    if 'analyze_data_checkbox' in locals():
        st.session_state.analyze_data_checkbox = analyze_data_checkbox
    
    if model:
        try:
            if st.session_state.transaction_data is not None and st.session_state.get('analyze_data_checkbox', False):
                # Perform data analysis
                detailed_analysis = analyze_data_for_question(
                    user_input, 
                    st.session_state.transaction_data,
                    st.session_state.dictionary_data
                )
                
                # Get column mappings between transaction data and dictionary
                transaction_columns = set(st.session_state.transaction_data.columns.tolist())
                dictionary_columns = set(st.session_state.column_descriptions.keys())
                
                # Find exact matches
                exact_matches = transaction_columns.intersection(dictionary_columns)
                
                # Find potential fuzzy matches for remaining columns
                unmatched_transaction_cols = transaction_columns - exact_matches
                unmatched_dictionary_cols = dictionary_columns - exact_matches
                
                fuzzy_matches = {}
                for t_col in unmatched_transaction_cols:
                    # Try simple normalization (lowercase, remove spaces, underscores)
                    normalized_t_col = t_col.lower().replace(' ', '').replace('_', '')
                    
                    for d_col in unmatched_dictionary_cols:
                        normalized_d_col = d_col.lower().replace(' ', '').replace('_', '')
                        
                        # Check for containment in either direction
                        if normalized_t_col in normalized_d_col or normalized_d_col in normalized_t_col:
                            fuzzy_matches[t_col] = d_col
                            break
                
                # Prepare transaction data column info with dictionary linkage
                transaction_info = "Transaction Data Information:\n"
                transaction_info += f"- Total Records: {len(st.session_state.transaction_data)}\n\n"
                
                # Add column information with mappings to dictionary
                transaction_info += "Column Information (with dictionary mappings):\n"
                for col in st.session_state.transaction_data.columns:
                    col_type = str(st.session_state.transaction_data[col].dtype)
                    
                    # Check for dictionary mapping (exact or fuzzy)
                    dict_col = None
                    mapping_type = ""
                    
                    if col in exact_matches:
                        dict_col = col
                        mapping_type = "(exact match)"
                    elif col in fuzzy_matches:
                        dict_col = fuzzy_matches[col]
                        mapping_type = "(fuzzy match)"
                    
                    if dict_col:
                        col_info = st.session_state.column_descriptions.get(dict_col, {})
                        col_description = col_info.get('description', "No description available") if isinstance(col_info, dict) else "No description available"
                        col_data_type = col_info.get('data_type', "") if isinstance(col_info, dict) else ""
                        
                        # Use the dictionary data type if available, otherwise use the pandas dtype
                        display_type = col_data_type if col_data_type else col_type
                        transaction_info += f"- {col} {mapping_type} (Type: {display_type}): {col_description}\n"
                    else:
                        transaction_info += f"- {col} (Type: {col_type}): No dictionary mapping available\n"
                
                # Add dictionary context using the formatted text
                dictionary_info = "Data Dictionary Information:\n"
                if st.session_state.dictionary_formatted_text:
                    dictionary_info += st.session_state.dictionary_formatted_text
                else:
                    dictionary_info += "No data dictionary provided.\n"
                
                # Identify important metrics and insights from the analysis
                insights = "Key Insights from Data Analysis:\n"
                
                # Check for date columns with time series data
                time_series_data = [key for key in detailed_analysis.keys() if key.startswith("monthly_")]
                if time_series_data:
                    insights += "- Time series data is available for temporal analysis.\n"
                
                # Check for correlations
                if "correlation_matrix" in detailed_analysis:
                    # Find strongest correlations
                    corr_matrix = detailed_analysis["correlation_matrix"]
                    strong_correlations = []
                    for col1 in corr_matrix:
                        for col2 in corr_matrix[col1]:
                            if col1 != col2 and abs(corr_matrix[col1][col2]) > 0.7:
                                strong_correlations.append((col1, col2, corr_matrix[col1][col2]))
                    
                    if strong_correlations:
                        insights += "- Strong correlations detected between:\n"
                        for col1, col2, corr in strong_correlations[:3]:  # Show top 3
                            insights += f"  * {col1} and {col2}: {corr:.2f}\n"
                
                # Generate AI response based on user input and data
                prompt = f"""
                You are an intelligent data analyst assistant. Answer the following question using the provided data:
                
                User Question: {user_input}
                
                {transaction_info}
                
                {dictionary_info}
                
                {insights}
                
                Detailed Analysis Data:
                ```json
                {json.dumps(detailed_analysis, indent=2)}
                ```
                
                Important Instructions:
                1. Provide a direct and concise answer based solely on the data provided
                2. Reference specific data points, trends, or patterns from the analysis to support your answer
                3. If you see time series data, discuss any trends over time
                4. Use the data dictionary definitions to correctly interpret columns
                5. If there are apparent relationships between variables, mention them
                6. If you cannot answer the question with the available data, explain exactly what data is missing
                7. Present any interesting insights you find, even if not directly asked
                8. If appropriate, suggest a visualization that would help illustrate your answer
                9. Format currency values with appropriate symbols if applicable
                10. Be precise with numbers - use exact figures from the data
                
                Your answer should be thorough yet concise, focusing on the most important insights related to the user's question.
                """
                
                # Generate response with the comprehensive prompt
                response = model.generate_content(prompt)
                bot_response = response.text
                
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
            elif st.session_state.transaction_data is None and st.session_state.get('analyze_data_checkbox', False):
                bot_response = "Please upload a transaction CSV file first by clicking the 'Toggle File Upload Section' button, then ask me to analyze it."
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
