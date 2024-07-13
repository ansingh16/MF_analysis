import streamlit as st
import pandas as pd
from multiprocessing import Pool

def find_closest_scheme(search_scheme, scheme_names):
    # Dummy implementation of find_closest_scheme function
    # Replace this with the actual implementation
    closest_scheme = (scheme_names.iloc[0].lower(), 0.9)  # Example closest scheme
    return closest_scheme

def process_scheme(search_scheme, df, units):
    closest_scheme = find_closest_scheme(search_scheme, df['Scheme Name'])
    closest_scheme_name = closest_scheme[0]
    closest_scheme_score = closest_scheme[1]

    # Find the row in the DataFrame that matches the closest scheme name
    matching_row = df[df['Scheme Name'].str.lower() == closest_scheme_name]

    # Display the results
    return {
        "Search Scheme": search_scheme,
        "Units": units,
        "Closest Scheme": closest_scheme_name,
        "Score": closest_scheme_score,
        "Matching Row": matching_row.to_dict(orient='records')
    }

st.header('OR')
st.header("Upload CSV File")
st.info("Please upload a CSV file with the following columns: 'Scheme Name', 'Units'")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    st.write("File uploaded successfully!")
    df = pd.read_csv(uploaded_file)
    st.write("Data Preview:")
    st.write(df)

if st.button("Add file", key="add_csv"):
    if uploaded_file is not None:
        try:
            # Read the uploaded file into a pandas DataFrame
            df = pd.read_csv(uploaded_file)
            st.write("File content:")
            st.write(df)
    
            # Check for required columns
            if 'Scheme Name' not in df.columns or 'Units' not in df.columns:
                st.error("CSV file must contain 'Scheme Name' and 'Units' columns.")
            else:
                # Use multiprocessing Pool to process schemes in parallel
                with Pool() as pool:
                    results = pool.starmap(process_scheme, [(search_scheme, df, units) for search_scheme, units in zip(df['Scheme Name'], df['Units'])])

                # Display results
                for result in results:
                    st.write(f"Search Scheme: {result['Search Scheme']}")
                    st.write(f"Units: {result['Units']}")
                    st.write(f"Closest Scheme: {result['Closest Scheme']} (Score: {result['Score']})")
                    st.write("Matching Row:")
                    st.write(pd.DataFrame(result['Matching Row']))
        except Exception as e:
            st.error(f"Error processing file: {e}")
