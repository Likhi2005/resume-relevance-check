import streamlit as st
from utils.api_client import APIClient

def upload_resume_page():
    st.title("📤 Upload Student Resumes")
    
    st.markdown("""
    Upload student resume files to evaluate them against job descriptions.
    Supported formats: **PDF** and **DOCX**
    """)
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="You can upload multiple resume files at once"
    )
    
    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} file(s):")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size} bytes)")
        
        if st.button("Upload Resumes", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            successful_uploads = 0
            failed_uploads = []
            
            for i, file in enumerate(uploaded_files):
                status_text.text(f"Uploading {file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Upload file
                file_data = file.read()
                result = st.session_state.api_client.upload_resume(file_data, file.name)
                
                if result and result.get('success'):
                    successful_uploads += 1
                else:
                    failed_uploads.append(file.name)
            
            # Show results
            status_text.empty()
            progress_bar.empty()
            
            if successful_uploads > 0:
                st.success(f"✅ Successfully uploaded {successful_uploads} resume(s)")
            
            if failed_uploads:
                st.error(f"❌ Failed to upload: {', '.join(failed_uploads)}")
            
            # Update stats
            try:
                stats = st.session_state.api_client.get_stats()
                if stats:
                    st.session_state.stats = stats
            except:
                pass
    
    # Show upload history/stats
    st.markdown("---")
    st.subheader("Upload Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Resumes Uploaded", st.session_state.stats.get('resumes', 0))
    with col2:
        if st.button("🔄 Refresh Stats"):
            try:
                stats = st.session_state.api_client.get_stats()
                if stats:
                    st.session_state.stats = stats
                    st.success("Stats refreshed!")
            except Exception as e:
                st.error(f"Error refreshing stats: {str(e)}")
    
    # Tips section
    with st.expander("💡 Tips for better results"):
        st.markdown("""
        - Ensure resume files are clear and well-formatted
        - PDF files generally work better than DOCX
        - Make sure the file size is reasonable (< 10MB)
        - Include relevant sections: Skills, Experience, Education, Projects
        """)