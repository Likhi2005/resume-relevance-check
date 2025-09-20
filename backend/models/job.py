from . import db
from datetime import datetime

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Job Details
    location = db.Column(db.String(100), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)  # Full-time, Internship, etc.
    experience_level = db.Column(db.String(50), nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    
    # Requirements
    required_skills = db.Column(db.JSON, nullable=True)
    preferred_skills = db.Column(db.JSON, nullable=True)
    education_requirements = db.Column(db.JSON, nullable=True)
    min_experience = db.Column(db.String(50), nullable=True)
    certifications = db.Column(db.JSON, nullable=True)
    languages = db.Column(db.String(200), nullable=True)
    
    # Metadata
    application_deadline = db.Column(db.Date, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100), nullable=True)  # placement team member
    status = db.Column(db.String(20), default='active')  # active, inactive, closed
    
    # Relationships
    evaluations = db.relationship('Evaluation', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'location': self.location,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'salary_range': self.salary_range,
            'department': self.department,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'education_requirements': self.education_requirements,
            'min_experience': self.min_experience,
            'certifications': self.certifications,
            'languages': self.languages,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'uploaded_by': self.uploaded_by,
            'status': self.status
        }