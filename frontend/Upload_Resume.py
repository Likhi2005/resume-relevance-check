import streamlit as st
from utils.api_client import APIClient

def upload_resume_page():
    st.title("📤 Upload Your Resume")
    
    st.markdown("""
    Upload your resume to check how well it matches available job opportunities.
    You'll receive a relevance score and personalized feedback for improvement.
    
    **Supported formats:** PDF and DOCX  
    **File size limit:** 10MB
    """)
    
    # Show available job opportunities first
    st.subheader("📋 Available Job Opportunities")
    try:
        jds = st.session_state.api_client.get_job_descriptions()
        if jds and jds.get('job_descriptions'):
            for i, jd in enumerate(jds['job_descriptions'][:5]):  # Show first 5
                with st.expander(f"🔹 {jd.get('title', 'Job Position')} - {jd.get('company', 'Company')}"):
                    st.write(f"**Skills Required:** {', '.join(jd.get('required_skills', [])[:5])}")
                    if jd.get('preview'):
                        st.caption(jd['preview'][:200] + "...")
            
            if len(jds['job_descriptions']) > 5:
                st.info(f"+ {len(jds['job_descriptions']) - 5} more job opportunities available")
        else:
            st.info("No job opportunities available at the moment.")
    except Exception as e:
        st.warning("Could not load job opportunities.")
    
    st.markdown("---")
    
    # Student information (optional)
    st.subheader("👨‍🎓 Student Information")
    col1, col2 = st.columns(2)
    
    with col1:
        student_name = st.text_input("Your Name")
        student_email = st.text_input("Email Address")
    
    with col2:
        student_id = st.text_input("Student ID (optional)")
        graduation_year = st.selectbox("Expected Graduation", 
                                     ["Select Year", "2024", "2025", "2026", "2027", "2028"])
    
    # File uploader
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=['pdf', 'docx'],
        help="Upload your latest resume in PDF or DOCX format"
    )
    
    if uploaded_file:
        # File info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"✅ File selected: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # Validation
        if file_size_mb > 10:
            st.error("❌ File size exceeds 10MB limit. Please upload a smaller file.")
            return
        
        # Upload button
        if st.button("🚀 Upload and Analyze Resume", type="primary", use_container_width=True):
            if not student_name or not student_email:
                st.error("Please provide your name and email address.")
                return
            
            with st.spinner("Uploading and analyzing your resume..."):
                # Prepare student data
                student_data = {
                    'name': student_name,
                    'email': student_email,
                    'student_id': student_id if student_id else None,
                    'graduation_year': graduation_year if graduation_year != "Select Year" else None
                }
                
                # Upload file with student data
                file_data = uploaded_file.read()
                result = st.session_state.api_client.upload_resume(
                    file_data, 
                    uploaded_file.name,
                    student_data=student_data
                )
                
                if result and result.get('success'):
                    st.success("✅ Resume uploaded and analyzed successfully!")
                    
                    # Show immediate feedback if available
                    if result.get('immediate_feedback'):
                        st.subheader("📊 Immediate Analysis Results")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Best Match Score", f"{result.get('best_score', 0):.1f}%")
                        with col2:
                            st.metric("Jobs Analyzed", result.get('jobs_analyzed', 0))
                        
                        if result.get('quick_feedback'):
                            st.markdown("**Quick Feedback:**")
                            st.info(result['quick_feedback'])
                        
                        st.markdown("💡 **Tip:** Go to 'My Results' to see detailed analysis for each job opportunity.")
                    
                    # Clear the form
                    st.balloons()
                else:
                    error_msg = result.get('error', 'Unknown error occurred') if result else 'Failed to upload resume'
                    st.error(f"❌ Upload failed: {error_msg}")
    
    # Previous uploads (if any)
    st.markdown("---")
    st.subheader("📚 Your Previous Uploads")
    
    try:
        # Get student's previous uploads
        student_uploads = st.session_state.api_client.get_student_uploads(student_email if 'student_email' in locals() else None)
        
        if student_uploads and student_uploads.get('uploads'):
            for upload in student_uploads['uploads'][-3:]:  # Show last 3
                with st.expander(f"📄 {upload.get('filename', 'Resume')} - {upload.get('upload_date', 'Unknown date')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Best Score:** {upload.get('best_score', 0):.1f}%")
                    with col2:
                        st.write(f"**Status:** {upload.get('status', 'Processed')}")
        else:
            st.info("No previous uploads found.")
    except:
        st.info("Login with your email to see previous uploads.")
    
    # Tips for students
    with st.expander("💡 Tips for Better Resume Analysis"):
        st.markdown("""
        **To get the best relevance scores:**
        
        - **Use relevant keywords** from job descriptions
        - **Include technical skills** specific to your field
        - **Highlight projects** that demonstrate practical experience
        - **Mention certifications** and courses you've completed
        - **Use clear section headers** (Skills, Experience, Education, Projects)
        - **Keep formatting consistent** and professional
        - **Include quantifiable achievements** where possible
        
        **Resume Sections to Include:**
        - Contact Information
        - Professional Summary/Objective
        - Technical Skills
        - Work Experience/Internships
        - Education
        - Projects
        - Certifications
        - Awards/Achievements
        """)


# import streamlit as st
# from utils.api_client import APIClient

# def upload_resume_page():
#     st.title("📤 Upload Student Resumes")
    
#     st.markdown("""
#     Upload student resume files to evaluate them against job descriptions.
#     Supported formats: **PDF** and **DOCX**
#     """)
    
#     # File uploader
#     uploaded_files = st.file_uploader(
#         "Choose resume files",
#         type=['pdf', 'docx'],
#         accept_multiple_files=True,
#         help="You can upload multiple resume files at once"
#     )
    
#     if uploaded_files:
#         st.write(f"Selected {len(uploaded_files)} file(s):")
#         for file in uploaded_files:
#             st.write(f"- {file.name} ({file.size} bytes)")
        
#         if st.button("Upload Resumes", type="primary"):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             successful_uploads = 0
#             failed_uploads = []
            
#             for i, file in enumerate(uploaded_files):
#                 status_text.text(f"Uploading {file.name}...")
#                 progress_bar.progress((i + 1) / len(uploaded_files))
                
#                 # Upload file
#                 file_data = file.read()
#                 result = st.session_state.api_client.upload_resume(file_data, file.name)
                
#                 if result and result.get('success'):
#                     successful_uploads += 1
#                 else:
#                     failed_uploads.append(file.name)
            
#             # Show results
#             status_text.empty()
#             progress_bar.empty()
            
#             if successful_uploads > 0:
#                 st.success(f"✅ Successfully uploaded {successful_uploads} resume(s)")
            
#             if failed_uploads:
#                 st.error(f"❌ Failed to upload: {', '.join(failed_uploads)}")
            
#             # Update stats
#             try:
#                 stats = st.session_state.api_client.get_stats()
#                 if stats:
#                     st.session_state.stats = stats
#             except:
#                 pass
    
#     # Show upload history/stats
#     st.markdown("---")
#     st.subheader("Upload Statistics")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("Total Resumes Uploaded", st.session_state.stats.get('resumes', 0))
#     with col2:
#         if st.button("🔄 Refresh Stats"):
#             try:
#                 stats = st.session_state.api_client.get_stats()
#                 if stats:
#                     st.session_state.stats = stats
#                     st.success("Stats refreshed!")
#             except Exception as e:
#                 st.error(f"Error refreshing stats: {str(e)}")
    
#     # Tips section
#     with st.expander("💡 Tips for better results"):
#         st.markdown("""
#         - Ensure resume files are clear and well-formatted
#         - PDF files generally work better than DOCX
#         - Make sure the file size is reasonable (< 10MB)
#         - Include relevant sections: Skills, Experience, Education, Projects
#         """)