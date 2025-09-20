import requests
import json
import streamlit as st

class APIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def upload_resume(self, file_data, filename):
        """Upload resume file to backend"""
        try:
            files = {'file': (filename, file_data, 'application/pdf')}
            response = requests.post(f"{self.base_url}/upload/resume", files=files)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def upload_jd(self, file_data=None, filename=None, text_content=None):
        """Upload job description file or text to backend"""
        try:
            if text_content:
                data = {'text': text_content}
                response = requests.post(f"{self.base_url}/upload/jd", json=data)
            else:
                files = {'file': (filename, file_data, 'application/pdf')}
                response = requests.post(f"{self.base_url}/upload/jd", files=files)
            
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_evaluations(self, filters=None):
        """Get evaluation results from backend"""
        try:
            params = filters or {}
            response = requests.get(f"{self.base_url}/evaluation", params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_evaluation_detail(self, resume_id, jd_id):
        """Get detailed evaluation for specific resume and JD"""
        try:
            response = requests.get(f"{self.base_url}/evaluation/{resume_id}/{jd_id}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_stats(self):
        """Get system statistics"""
        try:
            response = requests.get(f"{self.base_url}/stats")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_job_descriptions(self):
        """Get list of all job descriptions"""
        try:
            response = requests.get(f"{self.base_url}/job-descriptions")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None