from . import db
from datetime import datetime

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    content_text = db.Column(db.Text, nullable=True)
    
    # Parsed Information
    extracted_skills = db.Column(db.JSON, nullable=True)
    extracted_experience = db.Column(db.JSON, nullable=True)
    extracted_education = db.Column(db.JSON, nullable=True)
    extracted_projects = db.Column(db.JSON, nullable=True)
    extracted_certifications = db.Column(db.JSON, nullable=True)
    
    # Student Information
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    
    # Metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer, nullable=True)
    processing_status = db.Column(db.String(50), default='pending')  # pending, processed, error
    
    # Relationships
    evaluations = db.relationship('Evaluation', backref='resume', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'extracted_skills': self.extracted_skills,
            'extracted_experience': self.extracted_experience,
            'extracted_education': self.extracted_education,
            'extracted_projects': self.extracted_projects,
            'extracted_certifications': self.extracted_certifications,
            'student_id': self.student_id,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processing_status': self.processing_status
        }