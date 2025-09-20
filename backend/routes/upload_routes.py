from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
import time
import logging
from datetime import datetime
from models import db, Student, Resume, Job
from services.parser import DocumentParser
from services.matcher import ResumeJobMatcher
from services.scorer import RelevanceScorer
from services.feedback import FeedbackGenerator
from utils.embeddings import EmbeddingManager

upload_bp = Blueprint('upload', __name__)

# Initialize services
parser = DocumentParser()
matcher = ResumeJobMatcher()
scorer = RelevanceScorer()
feedback_generator = FeedbackGenerator()
embedding_manager = EmbeddingManager()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('/upload/resume', methods=['POST'])
def upload_resume():
    """Upload and process student resume"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF and DOCX files are allowed'}), 400
        
        # Get student data if provided
        student_data = None
        if 'student_data' in request.form:
            try:
                student_data = json.loads(request.form['student_data'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid student data format'}), 400
        
        # Create uploads directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save file with secure filename
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Handle student information
        student = None
        if student_data:
            # Check if student exists
            student = Student.query.filter_by(email=student_data['email']).first()
            if not student:
                # Create new student
                student = Student(
                    name=student_data.get('name'),
                    email=student_data.get('email'),
                    student_id=student_data.get('student_id'),
                    graduation_year=student_data.get('graduation_year')
                )
                db.session.add(student)
                db.session.commit()
        
        # Parse resume
        parsing_start = time.time()
        parsed_data = parser.parse_resume(file_path)
        parsing_time = time.time() - parsing_start
        
        if 'error' in parsed_data:
            return jsonify({'error': f'Failed to parse resume: {parsed_data["error"]}'}), 400
        
        # Save resume to database
        resume = Resume(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            content_text=parsed_data.get('clean_text', ''),
            extracted_skills=parsed_data.get('skills', []),
            extracted_experience=parsed_data.get('experience', []),
            extracted_education=parsed_data.get('education', []),
            extracted_projects=parsed_data.get('projects', []),
            extracted_certifications=parsed_data.get('certifications', []),
            student_id=student.id if student else None,
            file_size=os.path.getsize(file_path),
            processing_status='processed'
        )
        
        db.session.add(resume)
        db.session.commit()
        
        # Store resume embedding for future similarity searches
        embedding_manager.store_resume_embedding(
            resume.id, 
            parsed_data.get('clean_text', ''),
            {
                'student_id': student.id if student else None,
                'filename': filename,
                'skills': parsed_data.get('skills', [])[:10]  # Store top 10 skills
            }
        )
        
        # Get immediate feedback by evaluating against available jobs
        immediate_results = _evaluate_against_jobs(resume, parsed_data)
        
        response_data = {
            'success': True,
            'message': 'Resume uploaded and processed successfully',
            'resume_id': resume.id,
            'processing_time': round(parsing_time, 2),
            'extracted_data': {
                'skills_count': len(parsed_data.get('skills', [])),
                'experience_count': len(parsed_data.get('experience', [])),
                'education_count': len(parsed_data.get('education', [])),
                'projects_count': len(parsed_data.get('projects', [])),
                'certifications_count': len(parsed_data.get('certifications', []))
            }
        }
        
        # Add immediate results if available
        if immediate_results:
            response_data['immediate_feedback'] = immediate_results
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error uploading resume: {str(e)}")
        return jsonify({'error': 'Internal server error occurred while processing resume'}), 500

@upload_bp.route('/upload/jd', methods=['POST'])
def upload_job_description():
    """Upload and process job description"""
    try:
        job_metadata = None
        job_text = None
        
        # Handle JSON request (text content)
        if request.is_json:
            data = request.get_json()
            job_text = data.get('text', '')
            job_metadata = data.get('job_metadata', {})
            
            if not job_text.strip():
                return jsonify({'error': 'Job description text is required'}), 400
        
        # Handle file upload
        else:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Only PDF, DOCX, and TXT files are allowed'}), 400
            
            # Get job metadata if provided
            if 'job_metadata' in request.form:
                try:
                    job_metadata = json.loads(request.form['job_metadata'])
                except json.JSONDecodeError:
                    job_metadata = {}
            
            # Save and parse file
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            filename = f"jd_{timestamp}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Extract text from file
            if filename.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    job_text = f.read()
            else:
                job_text = parser.extract_text(file_path)
        
        if not job_text.strip():
            return jsonify({'error': 'Could not extract text from job description'}), 400
        
        # Parse job description
        parsing_start = time.time()
        parsed_jd = parser.parse_job_description(job_text)
        parsing_time = time.time() - parsing_start
        
        if 'error' in parsed_jd:
            return jsonify({'error': f'Failed to parse job description: {parsed_jd["error"]}'}), 400
        
        # Create job record
        job = Job(
            title=job_metadata.get('title', 'Untitled Position'),
            company=job_metadata.get('company', 'Unknown Company'),
            description=job_text,
            location=job_metadata.get('location'),
            job_type=job_metadata.get('job_type'),
            experience_level=job_metadata.get('experience_level'),
            salary_range=job_metadata.get('salary_range'),
            department=job_metadata.get('department'),
            required_skills=job_metadata.get('required_skills', []) + parsed_jd.get('required_skills', []),
            preferred_skills=job_metadata.get('preferred_skills', []),
            education_requirements=job_metadata.get('education_requirements', []),
            min_experience=job_metadata.get('min_experience'),
            certifications=job_metadata.get('certifications', []),
            languages=job_metadata.get('languages'),
            application_deadline=datetime.strptime(job_metadata['application_deadline'], '%Y-%m-%d').date() 
                                if job_metadata.get('application_deadline') else None,
            uploaded_by='placement_team',  # This should come from authentication
            status='active'
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Store job embedding
        embedding_manager.store_job_embedding(
            job.id,
            parsed_jd.get('clean_text', ''),
            {
                'title': job.title,
                'company': job.company,
                'required_skills': job.required_skills[:10]  # Store top 10 skills
            }
        )
        
        # Evaluate existing resumes against this job (async operation in production)
        pending_evaluations = _evaluate_job_against_resumes(job, parsed_jd)
        
        response_data = {
            'success': True,
            'message': 'Job description uploaded and processed successfully',
            'job_id': job.id,
            'processing_time': round(parsing_time, 2),
            'processing_results': {
                'skills_extracted': len(parsed_jd.get('required_skills', [])),
                'keywords_identified': len(job_text.split()),
                'resumes_pending': pending_evaluations
            },
            'preview': job_text[:200] + '...' if len(job_text) > 200 else job_text
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error uploading job description: {str(e)}")
        return jsonify({'error': 'Internal server error occurred while processing job description'}), 500

def _evaluate_against_jobs(resume: Resume, parsed_resume: dict) -> dict:
    """Evaluate resume against available jobs and return immediate feedback"""
    try:
        # Get active jobs
        jobs = Job.query.filter_by(status='active').limit(5).all()  # Limit to 5 for quick feedback
        
        if not jobs:
            return None
        
        best_score = 0
        best_job = None
        evaluations_created = 0
        
        for job in jobs:
            # Parse job if needed
            job_data = {
                'title': job.title,
                'company': job.company,
                'clean_text': job.description,
                'required_skills': job.required_skills or [],
                'preferred_skills': job.preferred_skills or []
            }
            
            # Perform matching
            match_results = matcher.comprehensive_match(parsed_resume, job_data)
            
            # Calculate score
            scoring_results = scorer.calculate_comprehensive_score(match_results)
            
            # Track best score
            if scoring_results['final_score'] > best_score:
                best_score = scoring_results['final_score']
                best_job = job
            
            # Create evaluation record (simplified for immediate feedback)
            from models.evaluation import Evaluation
            evaluation = Evaluation(
                resume_id=resume.id,
                job_id=job.id,
                relevance_score=scoring_results['final_score'],
                keyword_score=scoring_results['score_breakdown']['keyword_score'],
                semantic_score=scoring_results['score_breakdown']['semantic_score'],
                verdict=scoring_results['verdict'],
                missing_skills=match_results.get('exact_skill_match', {}).get('missing_skills', []),
                matched_skills=match_results.get('exact_skill_match', {}).get('matched_skills', []),
                evaluation_date=datetime.utcnow()
            )
            
            db.session.add(evaluation)
            evaluations_created += 1
        
        db.session.commit()
        
        return {
            'best_score': round(best_score, 1),
            'best_job': best_job.title if best_job else None,
            'jobs_analyzed': len(jobs),
            'evaluations_created': evaluations_created,
            'quick_feedback': f"Your resume shows {best_score:.1f}% relevance to available positions. "
                            f"Best match: {best_job.title if best_job else 'N/A'}"
        }
        
    except Exception as e:
        logging.error(f"Error in immediate evaluation: {str(e)}")
        return None

def _evaluate_job_against_resumes(job: Job, parsed_job: dict) -> int:
    """Evaluate job against existing resumes"""
    try:
        # Get all processed resumes
        resumes = Resume.query.filter_by(processing_status='processed').all()
        
        evaluations_created = 0
        
        for resume in resumes:
            # Parse resume data
            resume_data = {
                'clean_text': resume.content_text,
                'skills': resume.extracted_skills or [],
                'experience': resume.extracted_experience or [],
                'education': resume.extracted_education or [],
                'projects': resume.extracted_projects or [],
                'certifications': resume.extracted_certifications or []
            }
            
            # Perform matching
            match_results = matcher.comprehensive_match(resume_data, parsed_job)
            
            # Calculate score
            scoring_results = scorer.calculate_comprehensive_score(match_results)
            
            # Generate feedback
            feedback_text = feedback_generator.generate_personalized_feedback(
                resume_data, parsed_job, scoring_results, match_results
            )
            
            # Create evaluation record
            from models.evaluation import Evaluation
            evaluation = Evaluation(
                resume_id=resume.id,
                job_id=job.id,
                relevance_score=scoring_results['final_score'],
                keyword_score=scoring_results['score_breakdown']['keyword_score'],
                semantic_score=scoring_results['score_breakdown']['semantic_score'],
                verdict=scoring_results['verdict'],
                missing_skills=match_results.get('exact_skill_match', {}).get('missing_skills', []),
                missing_projects=[],  # Would be extracted from job requirements
                missing_certifications=[],  # Would be extracted from job requirements
                feedback=feedback_text,
                matched_skills=match_results.get('exact_skill_match', {}).get('matched_skills', []),
                evaluation_date=datetime.utcnow()
            )
            
            db.session.add(evaluation)
            evaluations_created += 1
        
        db.session.commit()
        return evaluations_created
        
    except Exception as e:
        logging.error(f"Error evaluating job against resumes: {str(e)}")
        return 0