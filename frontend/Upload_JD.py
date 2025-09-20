import streamlit as st
from utils.api_client import APIClient

def upload_jd_page():
    # Check if user is placement team
    if st.session_state.get('user_role') != 'placement':
        st.error("🚫 Access Denied: This page is only accessible to placement team members.")
        return
    
    st.title("📋 Upload Job Description")
    
    st.markdown("""
    Upload job descriptions to evaluate student resumes against specific role requirements.
    The system will analyze resumes and provide relevance scores and feedback.
    """)
    
    # Job Description Form
    st.subheader("📝 Job Description Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_title = st.text_input("Job Title *", placeholder="e.g., Software Engineer")
        company_name = st.text_input("Company Name *", placeholder="e.g., Tech Corp")
        location = st.text_input("Location", placeholder="e.g., Bangalore, India")
        job_type = st.selectbox("Job Type", ["Full-time", "Internship", "Part-time", "Contract"])
    
    with col2:
        experience_level = st.selectbox("Experience Level", 
                                      ["Entry Level", "Mid Level", "Senior Level", "Executive"])
        salary_range = st.text_input("Salary Range (optional)", placeholder="e.g., 5-8 LPA")
        application_deadline = st.date_input("Application Deadline (optional)")
        department = st.text_input("Department", placeholder="e.g., Engineering")
    
    # Skills section
    st.subheader("🛠️ Required Skills")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Must-have Skills** (Required)")
        required_skills = st.text_area(
            "Enter required skills (one per line)",
            height=150,
            placeholder="Python\nJavaScript\nReact\nSQL\nGit"
        )
    
    with col2:
        st.markdown("**Good-to-have Skills** (Preferred)")
        preferred_skills = st.text_area(
            "Enter preferred skills (one per line)",
            height=150,
            placeholder="AWS\nDocker\nKubernetes\nTypeScript\nGraphQL"
        )
    
    # Upload method selection
    st.subheader("📄 Job Description Content")
    upload_method = st.radio(
        "Choose input method:",
        ["Upload File", "Enter Text"],
        horizontal=True
    )
    
    jd_content = ""
    uploaded_file = None
    
    if upload_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload job description file",
            type=['pdf', 'docx', 'txt'],
            help="Upload a PDF, DOCX, or TXT file containing the job description"
        )
        
        if uploaded_file:
            st.success(f"✅ File selected: {uploaded_file.name}")
    
    else:  # Enter Text
        jd_content = st.text_area(
            "Job Description Content *",
            height=300,
            placeholder="""Enter the complete job description including:
- Job responsibilities
- Required qualifications
- Educational requirements
- Experience requirements
- Any specific technologies or tools
- Company culture and benefits""",
            help="Provide a comprehensive job description for better resume matching"
        )
        
        if jd_content:
            word_count = len(jd_content.split())
            st.caption(f"Word count: {word_count}")
    
    # Additional requirements
    st.subheader("🎓 Additional Requirements")
    col1, col2 = st.columns(2)
    
    with col1:
        education_req = st.multiselect(
            "Education Requirements",
            ["Bachelor's Degree", "Master's Degree", "PhD", "Diploma", "Certification"]
        )
        
        min_experience = st.selectbox(
            "Minimum Experience",
            ["0 years (Fresher)", "1+ years", "2+ years", "3+ years", "5+ years", "10+ years"]
        )
    
    with col2:
        certifications = st.text_area(
            "Preferred Certifications",
            placeholder="AWS Certified\nGoogle Cloud Certified\nCisco Certified",
            height=100
        )
        
        languages = st.text_input(
            "Language Requirements",
            placeholder="English, Hindi"
        )
    
    # Validation and Submit
    st.markdown("---")
    
    # Validate required fields
    can_submit = bool(job_title and company_name and (jd_content or uploaded_file))
    
    if not can_submit:
        st.warning("⚠️ Please fill in all required fields: Job Title, Company Name, and Job Description")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🚀 Upload Job Description", 
                    type="primary", 
                    disabled=not can_submit,
                    use_container_width=True):
            
            with st.spinner("Processing job description..."):
                # Prepare job data
                job_data = {
                    'title': job_title,
                    'company': company_name,
                    'location': location,
                    'job_type': job_type,
                    'experience_level': experience_level,
                    'salary_range': salary_range,
                    'department': department,
                    'required_skills': [skill.strip() for skill in required_skills.split('\n') if skill.strip()],
                    'preferred_skills': [skill.strip() for skill in preferred_skills.split('\n') if skill.strip()],
                    'education_requirements': education_req,
                    'min_experience': min_experience,
                    'certifications': [cert.strip() for cert in certifications.split('\n') if cert.strip()],
                    'languages': languages,
                    'application_deadline': str(application_deadline) if application_deadline else None
                }
                
                # Upload based on method
                if upload_method == "Upload File" and uploaded_file:
                    file_data = uploaded_file.read()
                    result = st.session_state.api_client.upload_jd(
                        file_data=file_data, 
                        filename=uploaded_file.name,
                        job_metadata=job_data
                    )
                else:
                    # Combine job data with content
                    full_content = f"""
Job Title: {job_title}
Company: {company_name}
Location: {location}
Job Type: {job_type}
Experience Level: {experience_level}

Required Skills: {', '.join(job_data['required_skills'])}
Preferred Skills: {', '.join(job_data['preferred_skills'])}

{jd_content}
"""
                    result = st.session_state.api_client.upload_jd(
                        text_content=full_content,
                        job_metadata=job_data
                    )
                
                if result and result.get('success'):
                    st.success("✅ Job description uploaded successfully!")
                    
                    # Show processing results
                    if result.get('processing_results'):
                        results = result['processing_results']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Skills Extracted", results.get('skills_extracted', 0))
                        with col2:
                            st.metric("Keywords Identified", results.get('keywords_identified', 0))
                        with col3:
                            st.metric("Resumes to Analyze", results.get('resumes_pending', 0))
                        
                        if results.get('resumes_pending', 0) > 0:
                            st.info(f"🔄 Analysis started for {results['resumes_pending']} existing resumes. Results will be available shortly.")
                    
                    st.balloons()
                    
                    # Option to upload another
                    if st.button("➕ Upload Another Job Description"):
                        st.rerun()
                        
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'Upload failed'
                    st.error(f"❌ Upload failed: {error_msg}")
    
    with col2:
        if st.button("🔄 Reset Form", use_container_width=True):
            st.rerun()
    
    # Show existing job descriptions
    st.markdown("---")
    st.subheader("📋 Existing Job Descriptions")
    
    try:
        jds = st.session_state.api_client.get_job_descriptions()
        if jds and jds.get('job_descriptions'):
            
            # Summary stats
            total_jds = len(jds['job_descriptions'])
            companies = list(set([jd.get('company', 'Unknown') for jd in jds['job_descriptions']]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Job Descriptions", total_jds)
            with col2:
                st.metric("Companies", len(companies))
            
            # Display recent JDs
            st.markdown("**Recent Job Descriptions:**")
            for i, jd in enumerate(jds['job_descriptions'][-5:]):  # Show last 5
                with st.expander(f"🔹 {jd.get('title', 'Untitled')} - {jd.get('company', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Location:** {jd.get('location', 'Not specified')}")
                        st.write(f"**Type:** {jd.get('job_type', 'Not specified')}")
                        st.write(f"**Experience:** {jd.get('experience_level', 'Not specified')}")
                    with col2:
                        if jd.get('required_skills'):
                            st.write(f"**Required Skills:** {', '.join(jd['required_skills'][:3])}...")
                        st.write(f"**Upload Date:** {jd.get('upload_date', 'Unknown')}")
                        st.write(f"**Status:** {jd.get('status', 'Active')}")
        else:
            st.info("No job descriptions uploaded yet.")
    except Exception as e:
        st.error(f"Error loading job descriptions: {str(e)}")
    
    # Tips section
    with st.expander("💡 Tips for Better Job Descriptions"):
        st.markdown("""
        **For accurate resume matching:**
        
        - **Be specific about technical skills** and tools required
        - **Include both required and preferred qualifications**
        - **Mention specific technologies, frameworks, and languages**
        - **Specify education and experience requirements clearly**
        - **Include information about projects or portfolio requirements**
        - **Add details about certifications that would be valuable**
        - **Use industry-standard terminology and keywords**
        - **Provide context about the role and responsibilities**
        
        **Well-structured job descriptions lead to better resume matching and more accurate feedback for students.**
        """)


# import streamlit as st
# from utils.api_client import APIClient

# def upload_jd_page():
#     st.title("📋 Upload Job Descriptions")
    
#     st.markdown("""
#     Upload job description files or paste job description text to match against student resumes.
#     Supported formats: **PDF**, **DOCX**, or **Plain Text**
#     """)
    
#     # Upload method selection
#     upload_method = st.radio(
#         "Choose upload method:",
#         ["Upload File", "Paste Text"],
#         horizontal=True
#     )
    
#     if upload_method == "Upload File":
#         uploaded_file = st.file_uploader(
#             "Choose job description file",
#             type=['pdf', 'docx'],
#             help="Upload a PDF or DOCX file containing the job description"
#         )
        
#         if uploaded_file:
#             st.write(f"Selected file: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
#             if st.button("Upload Job Description", type="primary"):
#                 with st.spinner("Uploading job description..."):
#                     file_data = uploaded_file.read()
#                     result = st.session_state.api_client.upload_jd(
#                         file_data=file_data, 
#                         filename=uploaded_file.name
#                     )
                    
#                     if result and result.get('success'):
#                         st.success("✅ Job description uploaded successfully!")
                        
#                         # Show parsed content preview if available
#                         if result.get('preview'):
#                             with st.expander("📄 Preview of parsed content"):
#                                 st.text_area(
#                                     "Job Description Content:",
#                                     result['preview'][:500] + "..." if len(result['preview']) > 500 else result['preview'],
#                                     height=150,
#                                     disabled=True
#                                 )
#                     else:
#                         st.error("❌ Failed to upload job description")
    
#     else:  # Paste Text
#         st.subheader("Paste Job Description Text")
        
#         job_title = st.text_input("Job Title (optional)")
#         company_name = st.text_input("Company Name (optional)")
        
#         jd_text = st.text_area(
#             "Job Description Text:",
#             height=300,
#             placeholder="Paste the complete job description here...",
#             help="Include all relevant details: requirements, skills, responsibilities, etc."
#         )
        
#         if jd_text.strip():
#             word_count = len(jd_text.split())
#             st.caption(f"Word count: {word_count}")
            
#             if st.button("Submit Job Description", type="primary"):
#                 with st.spinner("Processing job description..."):
#                     # Combine title and company with text if provided
#                     full_text = jd_text
#                     if job_title or company_name:
#                         header = []
#                         if job_title:
#                             header.append(f"Job Title: {job_title}")
#                         if company_name:
#                             header.append(f"Company: {company_name}")
#                         full_text = "\n".join(header) + "\n\n" + jd_text
                    
#                     result = st.session_state.api_client.upload_jd(text_content=full_text)
                    
#                     if result and result.get('success'):
#                         st.success("✅ Job description submitted successfully!")
                        
#                         # Clear the form
#                         st.session_state.jd_form_submitted = True
#                     else:
#                         st.error("❌ Failed to submit job description")
    
#     # Show current JD stats
#     st.markdown("---")
#     st.subheader("Job Description Statistics")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("Total Job Descriptions", st.session_state.stats.get('jds', 0))
#     with col2:
#         if st.button("🔄 Refresh Stats"):
#             try:
#                 stats = st.session_state.api_client.get_stats()
#                 if stats:
#                     st.session_state.stats = stats
#                     st.success("Stats refreshed!")
#             except Exception as e:
#                 st.error(f"Error refreshing stats: {str(e)}")
    
#     # Show existing job descriptions
#     with st.expander("📋 View Existing Job Descriptions"):
#         try:
#             jds = st.session_state.api_client.get_job_descriptions()
#             if jds and jds.get('job_descriptions'):
#                 for i, jd in enumerate(jds['job_descriptions']):
#                     st.write(f"**{i+1}.** {jd.get('title', 'Untitled')} - {jd.get('company', 'Unknown Company')}")
#                     if jd.get('preview'):
#                         st.caption(jd['preview'][:100] + "...")
#             else:
#                 st.info("No job descriptions uploaded yet.")
#         except Exception as e:
#             st.error(f"Error loading job descriptions: {str(e)}")
    
#     # Tips section
#     with st.expander("💡 Tips for better job descriptions"):
#         st.markdown("""
#         - Include clear job requirements and responsibilities
#         - List required and preferred skills
#         - Mention educational requirements
#         - Include experience level requirements
#         - Add information about projects or certifications needed
#         - Use industry-standard terminology and keywords
#         """)