# streamlit_app.py

import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime
from scraper import (
    fetch_html_selenium, 
    save_raw_data, 
    format_data, 
    save_formatted_data, 
    calculate_price,
    html_to_markdown_with_readability, 
    create_dynamic_listing_model,
    create_listings_container_model
)

# Initialize Streamlit app
st.set_page_config(page_title="GPT Integrated Selenium Web Scraper", layout="wide")
st.title("GPT Integrated Selenium Web Scraper 🦑")

# Sidebar components
st.sidebar.title("Web Scraper Settings")

# OpenAI API Key Input
api_key = st.sidebar.text_input(
    "Enter OpenAI API Key",
    type="password",
    help="Your OpenAI API key is used to authenticate requests to the OpenAI API."
)

# Model Selection
model_selection = st.sidebar.selectbox(
    "Select Model", 
    options=["gpt-4o-mini"], 
    index=0
)

# URL Input
url_input = st.sidebar.text_input(
    "Enter URL",
    value="https://news.ycombinator.com/",
    help="Enter the URL of the website you want to scrape."
)

# Tags input specifically in the sidebar
tags = st.sidebar.empty()  # Create an empty placeholder in the sidebar
tags = st_tags_sidebar(
    label='Enter Fields to Extract:',
    text='Press enter to add a field',
    value=['Title', 'Number of Points', 'Creator', 'Time Posted','Number of Places' , 'email', 'contact', 'Number of Comments'],
    suggestions=['Title', 'Number of Points', 'Creator', 'Time Posted','Number of Places' , 'email', 'contact', 'Number of Comments'],
    maxtags=-1,  # Set to -1 for unlimited tags
    key='tags_input'
)

st.sidebar.markdown("---")

# Process tags into a list
fields = tags

# Initialize variables to store token and cost information
input_tokens = output_tokens = total_cost = 0  # Default values

# Define the scraping function
def perform_scrape(api_key):
    if not api_key:
        st.error("Please enter your OpenAI API key to proceed.")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_html = fetch_html_selenium(url_input)
    markdown = html_to_markdown_with_readability(raw_html)
    save_raw_data(markdown, timestamp)
    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
    formatted_data = format_data(markdown, DynamicListingsContainer, api_key)
    formatted_data_text = json.dumps(formatted_data.dict())
    input_tokens, output_tokens, total_cost = calculate_price(markdown, formatted_data_text, model=model_selection)
    df = save_formatted_data(formatted_data, timestamp)

    return df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp

# Handling button press for scraping
if 'perform_scrape' not in st.session_state:
    st.session_state['perform_scrape'] = False

if st.sidebar.button("Scrape"):
    if not api_key:
        st.sidebar.error("OpenAI API key is required to perform scraping.")
    else:
        with st.spinner('Please wait... Data is being scraped.'):
            scrape_results = perform_scrape(api_key)
            if scrape_results:
                st.session_state['results'] = scrape_results
                st.session_state['perform_scrape'] = True

if st.session_state.get('perform_scrape'):
    results = st.session_state['results']
    if results:
        df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp = results
        # Display the DataFrame and other data
        st.header("Scraped Data")
        st.dataframe(df)

        st.sidebar.markdown("## Token Usage")
        st.sidebar.markdown(f"**Input Tokens:** {input_tokens}")
        st.sidebar.markdown(f"**Output Tokens:** {output_tokens}")
        st.sidebar.markdown(f"**Total Cost:** :green[**${total_cost:.4f}**]")

        # Create columns for download buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "Download JSON", 
                data=json.dumps(formatted_data.dict(), indent=4), 
                file_name=f"{timestamp}_data.json",
                mime="application/json"
            )
        with col2:
            # Convert formatted data to a dictionary if it's not already (assuming it has a .dict() method)
            data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data
            
            # Access the data under the dynamic key
            if isinstance(data_dict, dict) and len(data_dict) > 0:
                first_key = next(iter(data_dict))  # Safely get the first key
                main_data = data_dict[first_key]   # Access data using this key

                # Create DataFrame from the data
                df_download = pd.DataFrame(main_data)
                st.download_button(
                    "Download CSV", 
                    data=df_download.to_csv(index=False), 
                    file_name=f"{timestamp}_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data available to download as CSV.")
        with col3:
            st.download_button(
                "Download Markdown", 
                data=markdown, 
                file_name=f"{timestamp}_data.md",
                mime="text/markdown"
            )

# Optional: Display the markdown content
if st.checkbox("Show Raw Markdown"):
    if st.session_state.get('perform_scrape'):
        _, _, markdown, _, _, _, _ = st.session_state['results']
        st.markdown("### Raw Markdown Content")
        st.text(markdown)

# Command to run app 
# python3 -m streamlit run streamlit_app.py
