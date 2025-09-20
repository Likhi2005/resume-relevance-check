import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from Upload_Resume import upload_resume_page
from Upload_JD import upload_jd_page
from Results import results_page
from Search_Filter import search_filter_page

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient()

# Initialize session state variables
if 'stats' not in st.session_state:
    st.session_state.stats = {'resumes': 0, 'jds': 0, 'avg_score': 0}

def home_page():
    st.title("🎯 Automated Resume Relevance Check System")
    
    st.markdown("""
    ### Welcome to the Resume Relevance Checker!
    
    This system helps you evaluate how well student resumes match job descriptions and provides 
    personalized feedback for improvement.
    
    #### How to use:
    1. **Upload Job Descriptions** - Add job postings you want to match against
    2. **Upload Resumes** - Add student resumes for evaluation
    3. **View Results** - See relevance scores, verdicts, and improvement suggestions
    4. **Filter & Search** - Find specific results based on your criteria
    """)
    
    # Get stats from API
    try:
        stats = st.session_state.api_client.get_stats()
        if stats:
            st.session_state.stats = stats
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
    
    # Display stats in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📄 Uploaded Resumes",
            value=st.session_state.stats.get('resumes', 0)
        )
    
    with col2:
        st.metric(
            label="💼 Job Descriptions",
            value=st.session_state.stats.get('jds', 0)
        )
    
    with col3:
        st.metric(
            label="📊 Average Relevance Score",
            value=f"{st.session_state.stats.get('avg_score', 0):.1f}%"
        )
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Upload New Resume", use_container_width=True):
            st.session_state.current_page = "Upload Resume"
            st.rerun()
    
    with col2:
        if st.button("📋 Upload Job Description", use_container_width=True):
            st.session_state.current_page = "Upload JD"
            st.rerun()

def main():
    st.set_page_config(
        page_title="Resume Relevance Checker",
        page_icon="🎯",
        layout="wide"
    )
    
    # Initialize current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    pages = {
        "🏠 Home": "Home",
        "📤 Upload Resume": "Upload Resume", 
        "📋 Upload Job Description": "Upload JD",
        "📊 Results": "Results",
        "🔍 Search & Filter": "Search Filter"
    }
    
    selected_page = st.sidebar.selectbox(
        "Go to page:",
        list(pages.keys()),
        index=list(pages.values()).index(st.session_state.current_page)
    )
    
    st.session_state.current_page = pages[selected_page]
    
    # Route to appropriate page
    if st.session_state.current_page == "Home":
        home_page()
    elif st.session_state.current_page == "Upload Resume":
        upload_resume_page()
    elif st.session_state.current_page == "Upload JD":
        upload_jd_page()
    elif st.session_state.current_page == "Results":
        results_page()
    elif st.session_state.current_page == "Search Filter":
        search_filter_page()

if __name__ == "__main__":
    main()