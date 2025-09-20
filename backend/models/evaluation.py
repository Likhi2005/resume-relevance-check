from . import db
from datetime import datetime

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Scores
    relevance_score = db.Column(db.Float, nullable=False)
    keyword_score = db.Column(db.Float, nullable=True)
    semantic_score = db.Column(db.Float, nullable=True)
    
    # Verdict
    verdict = db.Column(db.String(20), nullable=False)  # High, Medium, Low
    
    # Missing Elements
    missing_skills = db.Column(db.JSON, nullable=True)
    missing_projects = db.Column(db.JSON, nullable=True)
    missing_certifications = db.Column(db.JSON, nullable=True)
    missing_experience = db.Column(db.JSON, nullable=True)
    
    # Feedback
    feedback = db.Column(db.Text, nullable=True)
    improvement_suggestions = db.Column(db.JSON, nullable=True)
    
    # Skill Matching Details
    matched_skills = db.Column(db.JSON, nullable=True)
    skill_gaps = db.Column(db.JSON, nullable=True)
    
    # Metadata
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    processing_time = db.Column(db.Float, nullable=True)  # seconds
    
    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'job_id': self.job_id,
            'relevance_score': self.relevance_score,
            'keyword_score': self.keyword_score,
            'semantic_score': self.semantic_score,
            'verdict': self.verdict,
            'missing_skills': self.missing_skills,
            'missing_projects': self.missing_projects,
            'missing_certifications': self.missing_certifications,
            'missing_experience': self.missing_experience,
            'feedback': self.feedback,
            'improvement_suggestions': self.improvement_suggestions,
            'matched_skills': self.matched_skills,
            'skill_gaps': self.skill_gaps,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'processing_time': self.processing_time
        }