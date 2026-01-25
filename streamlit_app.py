import streamlit as st
import requests
import os


# Configure page
st.set_page_config(page_title="Log Pipeline Search", page_icon="🔍", layout="wide")

# Initialize session state
if "file_indexed" not in st.session_state:
    st.session_state.file_indexed = False
if "current_source" not in st.session_state:
    st.session_state.current_source = ""

st.title("🔍 Mini Telemetry Pipeline Search")

# API endpoint - configurable for both Docker and local development
API_URL = os.getenv("API_URL", "http://localhost:8000")


# File Upload Section
st.header("📂 Upload Log File")

uploaded_file = st.file_uploader(
    "Choose a log file to upload and index",
    type=["log", "txt", "json"],
    help="Upload log files in .log, .txt, or .json format"
)

if uploaded_file is not None:
    # Show file details
    st.write(f"**File name:** {uploaded_file.name}")
    st.write(f"**File size:** {uploaded_file.size} bytes")
    
    if st.button("📤 Upload and Index File"):
        try:
            # Prepare the file for upload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            with st.spinner("Uploading and indexing file..."):
                response = requests.post(f"{API_URL}/upload-file", files=files)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ File uploaded and indexed successfully!")
                
                # Set session state
                st.session_state.file_indexed = True
                st.session_state.current_source = result.get("source", "")
                
                # Display stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lines Processed", result.get("lines_processed", 0))
                with col2:
                    st.metric("Logs Indexed", result.get("logs_indexed", 0))
                with col3:
                    st.metric("Source", result.get("source", "N/A"))
                
                st.info("💡 You can now search for logs using the search box below")
            else:
                st.error(f"❌ Upload failed: {response.status_code} - {response.text}")
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the backend is running on port 8000.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.divider()

# Sidebar for source filter
st.sidebar.header("Filters")
# Auto-fill source filter with current source from session state
source = st.sidebar.text_input("Source (optional)", value=st.session_state.current_source)

# Main search interface

# Show warning if file not indexed
if not st.session_state.file_indexed:
    st.warning("⚠️ Upload and index a file before searching.")

search_query = st.text_input("Search logs:", placeholder="e.g., database error, authentication failed")

search_button = st.button("🔍 Search")

# Display results
if search_button and search_query and st.session_state.file_indexed:
    try:
        # Make API request
        params = {"q": search_query}
        if source:
            params["source"] = source
        
        response = requests.get(f"{API_URL}/search", params=params)
        
        if response.status_code == 200:
            results = response.json()
            
            st.success(f"Found {len(results)} matching logs")
            
            # Display results
            for i, log in enumerate(results, 1):
                with st.expander(f"#{i} - {log.get('level', 'N/A')} - {log.get('timestamp', 'N/A')}"):
                    st.write(f"**Level:** {log.get('level', 'N/A')}")
                    st.write(f"**Timestamp:** {log.get('timestamp', 'N/A')}")
                    if log.get('source'):
                        st.write(f"**Source:** {log.get('source')}")
                    st.write(f"**Message:** {log.get('message', 'N/A')}")
        else:
            st.error(f"API error: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the backend is running on port 8000.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


# Stats section
st.sidebar.header("Stats")

if st.sidebar.button("Refresh Stats"):
    try:
        params = {}
        if source:
            params["source"] = source
        
        # Get summary
        summary_response = requests.get(f"{API_URL}/summary", params=params)
        
        if summary_response.status_code == 200:
            summary = summary_response.json()
            
            st.sidebar.metric("Total Logs", summary.get("total", 0))
            
            st.sidebar.write("**By Level:**")
            for level, count in summary.get("by_level", {}).items():
                st.sidebar.write(f"- {level}: {count}")
    
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Cannot connect to API")
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")


# Instructions
st.sidebar.markdown("---")
st.sidebar.markdown("""
### How to use:
1. Start the API: `uvicorn src.api:app --reload`
2. Enter search query
3. Optionally filter by source
4. Click Search
""")
