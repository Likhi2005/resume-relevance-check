import streamlit as st
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

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login_page():
    st.title("🎯 Resume Relevance Check System")
    st.markdown("### Please select your role to continue")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='padding: 20px; border: 2px solid #007bff; border-radius: 10px; text-align: center;'>
        <h3>👨‍🎓 Student Portal</h3>
        <p>Upload your resume and check relevance against job opportunities</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Login as Student", use_container_width=True, type="primary"):
            st.session_state.user_role = "student"
            st.session_state.authenticated = True
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style='padding: 20px; border: 2px solid #28a745; border-radius: 10px; text-align: center;'>
        <h3>👔 Placement Team</h3>
        <p>Upload job descriptions and manage recruitment process</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Simple authentication for placement team
        with st.expander("Placement Team Login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login as Placement Team", use_container_width=True):
                # Simple authentication (replace with your actual auth logic)
                if username == "placement" and password == "admin123":
                    st.session_state.user_role = "placement"
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

def student_dashboard():
    st.title("👨‍🎓 Student Portal")
    
    st.markdown("""
    ### Welcome to the Resume Relevance Checker!
    
    Upload your resume to check how well it matches available job opportunities and get 
    personalized feedback for improvement.
    
    #### What you can do:
    - 📤 **Upload Resume** - Submit your resume for evaluation
    - 📊 **View Results** - See your relevance scores and feedback
    - 🔍 **Search Opportunities** - Find jobs that match your profile
    """)
    
    # Student stats (only their own data)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get student's uploaded resumes count
        st.metric("Your Resumes", st.session_state.stats.get('student_resumes', 0))
    
    with col2:
        # Available job opportunities
        st.metric("Available Jobs", st.session_state.stats.get('jds', 0))
    
    with col3:
        # Student's best score
        st.metric("Your Best Score", f"{st.session_state.stats.get('student_best_score', 0):.1f}%")
    
    st.markdown("---")
    
    # Quick actions for students
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Upload Your Resume", use_container_width=True, type="primary"):
            st.session_state.current_page = "Upload Resume"
            st.rerun()
    
    with col2:
        if st.button("📊 View Your Results", use_container_width=True):
            st.session_state.current_page = "Results"
            st.rerun()

def placement_dashboard():
    st.title("👔 Placement Team Dashboard")
    
    st.markdown("""
    ### Welcome to the Placement Management System!
    
    Manage job descriptions, evaluate student resumes, and streamline your recruitment process.
    
    #### What you can do:
    - 📋 **Upload Job Descriptions** - Add new job opportunities
    - 📊 **View All Results** - See all student evaluations
    - 🔍 **Search & Filter** - Find the best candidates
    """)
    
    # Get stats from API
    try:
        stats = st.session_state.api_client.get_stats()
        if stats:
            st.session_state.stats = stats
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
    
    # Placement team stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Resumes", st.session_state.stats.get('resumes', 0))
    
    with col2:
        st.metric("Job Descriptions", st.session_state.stats.get('jds', 0))
    
    with col3:
        st.metric("Average Score", f"{st.session_state.stats.get('avg_score', 0):.1f}%")
    
    with col4:
        high_performers = st.session_state.stats.get('high_performers', 0)
        st.metric("High Performers", high_performers)
    
    st.markdown("---")
    
    # Quick actions for placement team
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Upload Job Description", use_container_width=True, type="primary"):
            st.session_state.current_page = "Upload JD"
            st.rerun()
    
    with col2:
        if st.button("📊 View All Results", use_container_width=True):
            st.session_state.current_page = "Results"
            st.rerun()
    
    with col3:
        if st.button("🔍 Advanced Search", use_container_width=True):
            st.session_state.current_page = "Search Filter"
            st.rerun()

def main():
    st.set_page_config(
        page_title="Resume Relevance Checker",
        page_icon="🎯",
        layout="wide"
    )
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Initialize current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    # Sidebar with logout and navigation
    with st.sidebar:
        st.title("Navigation")
        
        # User info
        role_emoji = "👨‍🎓" if st.session_state.user_role == "student" else "👔"
        st.markdown(f"**{role_emoji} {st.session_state.user_role.title()} Portal**")
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.current_page = "Dashboard"
            st.rerun()
        
        st.markdown("---")
        
        # Role-based navigation
        if st.session_state.user_role == "student":
            pages = {
                "🏠 Dashboard": "Dashboard",
                "📤 Upload Resume": "Upload Resume",
                "📊 My Results": "Results",
                "🔍 Find Jobs": "Search Filter"
            }
        else:  # placement team
            pages = {
                "🏠 Dashboard": "Dashboard",
                "📋 Upload Job Description": "Upload JD",
                "📊 All Results": "Results",
                "🔍 Search & Filter": "Search Filter"
            }
        
        selected_page = st.selectbox(
            "Go to page:",
            list(pages.keys()),
            index=list(pages.values()).index(st.session_state.current_page)
        )
        
        st.session_state.current_page = pages[selected_page]
    
    # Route to appropriate page based on role
    if st.session_state.current_page == "Dashboard":
        if st.session_state.user_role == "student":
            student_dashboard()
        else:
            placement_dashboard()
    elif st.session_state.current_page == "Upload Resume":
        if st.session_state.user_role == "student":
            upload_resume_page()
        else:
            st.error("Access denied. Students only.")
    elif st.session_state.current_page == "Upload JD":
        if st.session_state.user_role == "placement":
            upload_jd_page()
        else:
            st.error("Access denied. Placement team only.")
    elif st.session_state.current_page == "Results":
        results_page()
    elif st.session_state.current_page == "Search Filter":
        search_filter_page()

if __name__ == "__main__":
    main()

# import streamlit as st
# import pandas as pd
# from utils.api_client import APIClient
# from Upload_Resume import upload_resume_page
# from Upload_JD import upload_jd_page
# from Results import results_page
# from Search_Filter import search_filter_page

# # Initialize API client
# if 'api_client' not in st.session_state:
#     st.session_state.api_client = APIClient()

# # Initialize session state variables
# if 'stats' not in st.session_state:
#     st.session_state.stats = {'resumes': 0, 'jds': 0, 'avg_score': 0}

# def home_page():
#     st.title("🎯 Automated Resume Relevance Check System")
    
#     st.markdown("""
#     ### Welcome to the Resume Relevance Checker!
    
#     This system helps you evaluate how well student resumes match job descriptions and provides 
#     personalized feedback for improvement.
    
#     #### How to use:
#     1. **Upload Job Descriptions** - Add job postings you want to match against
#     2. **Upload Resumes** - Add student resumes for evaluation
#     3. **View Results** - See relevance scores, verdicts, and improvement suggestions
#     4. **Filter & Search** - Find specific results based on your criteria
#     """)
    
#     # Get stats from API
#     try:
#         stats = st.session_state.api_client.get_stats()
#         if stats:
#             st.session_state.stats = stats
#     except Exception as e:
#         st.error(f"Error fetching stats: {str(e)}")
    
#     # Display stats in columns
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.metric(
#             label="📄 Uploaded Resumes",
#             value=st.session_state.stats.get('resumes', 0)
#         )
    
#     with col2:
#         st.metric(
#             label="💼 Job Descriptions",
#             value=st.session_state.stats.get('jds', 0)
#         )
    
#     with col3:
#         st.metric(
#             label="📊 Average Relevance Score",
#             value=f"{st.session_state.stats.get('avg_score', 0):.1f}%"
#         )
    
#     st.markdown("---")
    
#     # Quick actions
#     st.subheader("Quick Actions")
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("📤 Upload New Resume", use_container_width=True):
#             st.session_state.current_page = "Upload Resume"
#             st.rerun()
    
#     with col2:
#         if st.button("📋 Upload Job Description", use_container_width=True):
#             st.session_state.current_page = "Upload JD"
#             st.rerun()

# def main():
#     st.set_page_config(
#         page_title="Resume Relevance Checker",
#         page_icon="🎯",
#         layout="wide"
#     )
    
#     # Initialize current page
#     if 'current_page' not in st.session_state:
#         st.session_state.current_page = "Home"
    
#     # Sidebar navigation
#     st.sidebar.title("Navigation")
#     pages = {
#         "🏠 Home": "Home",
#         "📤 Upload Resume": "Upload Resume", 
#         "📋 Upload Job Description": "Upload JD",
#         "📊 Results": "Results",
#         "🔍 Search & Filter": "Search Filter"
#     }
    
#     selected_page = st.sidebar.selectbox(
#         "Go to page:",
#         list(pages.keys()),
#         index=list(pages.values()).index(st.session_state.current_page)
#     )
    
#     st.session_state.current_page = pages[selected_page]
    
#     # Route to appropriate page
#     if st.session_state.current_page == "Home":
#         home_page()
#     elif st.session_state.current_page == "Upload Resume":
#         upload_resume_page()
#     elif st.session_state.current_page == "Upload JD":
#         upload_jd_page()
#     elif st.session_state.current_page == "Results":
#         results_page()
#     elif st.session_state.current_page == "Search Filter":
#         search_filter_page()

# if __name__ == "__main__":
#     main()