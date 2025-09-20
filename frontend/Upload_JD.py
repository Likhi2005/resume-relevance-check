import streamlit as st
from utils.api_client import APIClient

def upload_jd_page():
    st.title("📋 Upload Job Descriptions")
    
    st.markdown("""
    Upload job description files or paste job description text to match against student resumes.
    Supported formats: **PDF**, **DOCX**, or **Plain Text**
    """)
    
    # Upload method selection
    upload_method = st.radio(
        "Choose upload method:",
        ["Upload File", "Paste Text"],
        horizontal=True
    )
    
    if upload_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose job description file",
            type=['pdf', 'docx'],
            help="Upload a PDF or DOCX file containing the job description"
        )
        
        if uploaded_file:
            st.write(f"Selected file: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            if st.button("Upload Job Description", type="primary"):
                with st.spinner("Uploading job description..."):
                    file_data = uploaded_file.read()
                    result = st.session_state.api_client.upload_jd(
                        file_data=file_data, 
                        filename=uploaded_file.name
                    )
                    
                    if result and result.get('success'):
                        st.success("✅ Job description uploaded successfully!")
                        
                        # Show parsed content preview if available
                        if result.get('preview'):
                            with st.expander("📄 Preview of parsed content"):
                                st.text_area(
                                    "Job Description Content:",
                                    result['preview'][:500] + "..." if len(result['preview']) > 500 else result['preview'],
                                    height=150,
                                    disabled=True
                                )
                    else:
                        st.error("❌ Failed to upload job description")
    
    else:  # Paste Text
        st.subheader("Paste Job Description Text")
        
        job_title = st.text_input("Job Title (optional)")
        company_name = st.text_input("Company Name (optional)")
        
        jd_text = st.text_area(
            "Job Description Text:",
            height=300,
            placeholder="Paste the complete job description here...",
            help="Include all relevant details: requirements, skills, responsibilities, etc."
        )
        
        if jd_text.strip():
            word_count = len(jd_text.split())
            st.caption(f"Word count: {word_count}")
            
            if st.button("Submit Job Description", type="primary"):
                with st.spinner("Processing job description..."):
                    # Combine title and company with text if provided
                    full_text = jd_text
                    if job_title or company_name:
                        header = []
                        if job_title:
                            header.append(f"Job Title: {job_title}")
                        if company_name:
                            header.append(f"Company: {company_name}")
                        full_text = "\n".join(header) + "\n\n" + jd_text
                    
                    result = st.session_state.api_client.upload_jd(text_content=full_text)
                    
                    if result and result.get('success'):
                        st.success("✅ Job description submitted successfully!")
                        
                        # Clear the form
                        st.session_state.jd_form_submitted = True
                    else:
                        st.error("❌ Failed to submit job description")
    
    # Show current JD stats
    st.markdown("---")
    st.subheader("Job Description Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Job Descriptions", st.session_state.stats.get('jds', 0))
    with col2:
        if st.button("🔄 Refresh Stats"):
            try:
                stats = st.session_state.api_client.get_stats()
                if stats:
                    st.session_state.stats = stats
                    st.success("Stats refreshed!")
            except Exception as e:
                st.error(f"Error refreshing stats: {str(e)}")
    
    # Show existing job descriptions
    with st.expander("📋 View Existing Job Descriptions"):
        try:
            jds = st.session_state.api_client.get_job_descriptions()
            if jds and jds.get('job_descriptions'):
                for i, jd in enumerate(jds['job_descriptions']):
                    st.write(f"**{i+1}.** {jd.get('title', 'Untitled')} - {jd.get('company', 'Unknown Company')}")
                    if jd.get('preview'):
                        st.caption(jd['preview'][:100] + "...")
            else:
                st.info("No job descriptions uploaded yet.")
        except Exception as e:
            st.error(f"Error loading job descriptions: {str(e)}")
    
    # Tips section
    with st.expander("💡 Tips for better job descriptions"):
        st.markdown("""
        - Include clear job requirements and responsibilities
        - List required and preferred skills
        - Mention educational requirements
        - Include experience level requirements
        - Add information about projects or certifications needed
        - Use industry-standard terminology and keywords
        """)