import requests
import json
import streamlit as st

class APIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def upload_resume(self, file_data, filename, student_data=None):
        """Upload resume file to backend with student information"""
        try:
            files = {'file': (filename, file_data, 'application/pdf')}
            data = {'student_data': json.dumps(student_data)} if student_data else {}
            
            response = requests.post(f"{self.base_url}/upload/resume", files=files, data=data)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def upload_jd(self, file_data=None, filename=None, text_content=None, job_metadata=None):
        """Upload job description file or text to backend with metadata"""
        try:
            if text_content:
                data = {
                    'text': text_content,
                    'job_metadata': job_metadata
                }
                response = requests.post(f"{self.base_url}/upload/jd", json=data)
            else:
                files = {'file': (filename, file_data, 'application/pdf')}
                data = {'job_metadata': json.dumps(job_metadata)} if job_metadata else {}
                response = requests.post(f"{self.base_url}/upload/jd", files=files, data=data)
            
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_evaluations(self, filters=None, student_email=None):
        """Get evaluation results from backend"""
        try:
            params = filters or {}
            if student_email:
                params['student_email'] = student_email
            
            response = requests.get(f"{self.base_url}/evaluation", params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def get_student_uploads(self, student_email):
        """Get student's previous uploads"""
        try:
            if not student_email:
                return None
            response = requests.get(f"{self.base_url}/student/uploads", params={'email': student_email})
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
    
    def authenticate_placement_team(self, username, password):
        """Authenticate placement team member"""
        try:
            data = {'username': username, 'password': password}
            response = requests.post(f"{self.base_url}/auth/placement", json=data)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Authentication Error: {str(e)}")
            return None
    
    def regenerate_evaluation(self, evaluation_id):
        """Regenerate evaluation with updated algorithms"""
        try:
            response = requests.post(f"{self.base_url}/evaluation/regenerate/{evaluation_id}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def health_check(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            return None