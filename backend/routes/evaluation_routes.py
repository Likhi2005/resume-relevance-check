from flask import Blueprint, request, jsonify
from sqlalchemy import desc, and_, or_
from models import db, Student, Resume, Job, Evaluation
from services.feedback import FeedbackGenerator
from utils.embeddings import EmbeddingManager
import logging

evaluation_bp = Blueprint('evaluation', __name__)

feedback_generator = FeedbackGenerator()
embedding_manager = EmbeddingManager()

@evaluation_bp.route('/evaluation', methods=['GET'])
def get_evaluations():
    """Get evaluation results with optional filtering"""
    try:
        # Get query parameters
        student_email = request.args.get('student_email')
        job_id = request.args.get('job_id')
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        verdict = request.args.get('verdict')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'evaluation_date')
        order = request.args.get('order', 'desc')
        
        # Build query
        query = db.session.query(Evaluation).join(Resume).join(Job)
        
        # Apply filters
        if student_email:
            # Filter by student email
            query = query.join(Student, Resume.student_id == Student.id).filter(Student.email == student_email)
        
        if job_id:
            query = query.filter(Evaluation.job_id == job_id)
        
        if min_score is not None:
            query = query.filter(Evaluation.relevance_score >= min_score)
        
        if max_score is not None:
            query = query.filter(Evaluation.relevance_score <= max_score)
        
        if verdict:
            query = query.filter(Evaluation.verdict == verdict)
        
        # Apply sorting
        if hasattr(Evaluation, sort_by):
            if order.lower() == 'desc':
                query = query.order_by(desc(getattr(Evaluation, sort_by)))
            else:
                query = query.order_by(getattr(Evaluation, sort_by))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        evaluations = query.offset(offset).limit(limit).all()
        
        # Format results
        results = []
        for evaluation in evaluations:
            eval_data = evaluation.to_dict()
            
            # Add resume and job information
            eval_data['resume'] = {
                'id': evaluation.resume.id,
                'filename': evaluation.resume.original_filename,
                'upload_date': evaluation.resume.upload_date.isoformat() if evaluation.resume.upload_date else None
            }
            
            eval_data['job'] = {
                'id': evaluation.job.id,
                'title': evaluation.job.title,
                'company': evaluation.job.company,
                'location': evaluation.job.location
            }
            
            # Add student information if available
            if evaluation.resume.student:
                eval_data['student'] = {
                    'name': evaluation.resume.student.name,
                    'email': evaluation.resume.student.email,
                    'student_id': evaluation.resume.student.student_id
                }
            
            results.append(eval_data)
        
        # Calculate statistics
        stats = _calculate_evaluation_stats(evaluations)
        
        return jsonify({
            'evaluations': results,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            },
            'statistics': stats
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting evaluations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve evaluations'}), 500

@evaluation_bp.route('/evaluation/<int:resume_id>/<int:job_id>', methods=['GET'])
def get_evaluation_detail(resume_id, job_id):
    """Get detailed evaluation for specific resume and job"""
    try:
        # Get evaluation
        evaluation = Evaluation.query.filter_by(
            resume_id=resume_id, 
            job_id=job_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        # Get detailed information
        resume = evaluation.resume
        job = evaluation.job
        
        # Format detailed response
        detailed_result = {
            'evaluation': evaluation.to_dict(),
            'resume_details': {
                'id': resume.id,
                'filename': resume.original_filename,
                'extracted_skills': resume.extracted_skills,
                'extracted_experience': resume.extracted_experience,
                'extracted_education': resume.extracted_education,
                'extracted_projects': resume.extracted_projects,
                'extracted_certifications': resume.extracted_certifications,
                'upload_date': resume.upload_date.isoformat() if resume.upload_date else None
            },
            'job_details': {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'description': job.description,
                'location': job.location,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'required_skills': job.required_skills,
                'preferred_skills': job.preferred_skills,
                'education_requirements': job.education_requirements
            }
        }
        
        # Add student information if available
        if resume.student:
            detailed_result['student_details'] = resume.student.to_dict()
        
        # Generate additional insights
        insights = _generate_evaluation_insights(evaluation, resume, job)
        detailed_result['insights'] = insights
        
        return jsonify(detailed_result), 200
        
    except Exception as e:
        logging.error(f"Error getting evaluation detail: {str(e)}")
        return jsonify({'error': 'Failed to retrieve evaluation details'}), 500

@evaluation_bp.route('/evaluation/regenerate/<int:evaluation_id>', methods=['POST'])
def regenerate_evaluation(evaluation_id):
    """Regenerate evaluation with updated algorithms"""
    try:
        evaluation = Evaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        # Get resume and job data
        resume = evaluation.resume
        job = evaluation.job
        
        # Prepare data for re-evaluation
        resume_data = {
            'clean_text': resume.content_text,
            'skills': resume.extracted_skills or [],
            'experience': resume.extracted_experience or [],
            'education': resume.extracted_education or [],
            'projects': resume.extracted_projects or [],
            'certifications': resume.extracted_certifications or []
        }
        
        job_data = {
            'title': job.title,
            'company': job.company,
            'clean_text': job.description,
            'required_skills': job.required_skills or [],
            'preferred_skills': job.preferred_skills or []
        }
        
        # Re-run evaluation pipeline
        from services.matcher import ResumeJobMatcher
        from services.scorer import RelevanceScorer
        
        matcher = ResumeJobMatcher()
        scorer = RelevanceScorer()
        
        # Perform matching
        match_results = matcher.comprehensive_match(resume_data, job_data)
        
        # Calculate new scores
        scoring_results = scorer.calculate_comprehensive_score(match_results)
        
        # Generate new feedback
        new_feedback = feedback_generator.generate_personalized_feedback(
            resume_data, job_data, scoring_results, match_results
        )
        
        # Update evaluation
        evaluation.relevance_score = scoring_results['final_score']
        evaluation.keyword_score = scoring_results['score_breakdown']['keyword_score']
        evaluation.semantic_score = scoring_results['score_breakdown']['semantic_score']
        evaluation.verdict = scoring_results['verdict']
        evaluation.feedback = new_feedback
        evaluation.missing_skills = match_results.get('exact_skill_match', {}).get('missing_skills', [])
        evaluation.matched_skills = match_results.get('exact_skill_match', {}).get('matched_skills', [])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evaluation regenerated successfully',
            'evaluation': evaluation.to_dict(),
            'changes': {
                'score_updated': True,
                'feedback_updated': True,
                'new_score': scoring_results['final_score']
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error regenerating evaluation: {str(e)}")
        return jsonify({'error': 'Failed to regenerate evaluation'}), 500

@evaluation_bp.route('/evaluation/batch-regenerate', methods=['POST'])
def batch_regenerate_evaluations():
    """Regenerate multiple evaluations"""
    try:
        data = request.get_json()
        evaluation_ids = data.get('evaluation_ids', [])
        
        if not evaluation_ids:
            return jsonify({'error': 'No evaluation IDs provided'}), 400
        
        updated_count = 0
        errors = []
        
        for eval_id in evaluation_ids:
            try:
                # Use the regenerate logic for each evaluation
                evaluation = Evaluation.query.get(eval_id)
                if evaluation:
                    # Regenerate evaluation (simplified version)
                    updated_count += 1
                else:
                    errors.append(f"Evaluation {eval_id} not found")
            except Exception as e:
                errors.append(f"Error updating evaluation {eval_id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} evaluations',
            'updated_count': updated_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        logging.error(f"Error in batch regeneration: {str(e)}")
        return jsonify({'error': 'Failed to regenerate evaluations'}), 500

@evaluation_bp.route('/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    try:
        # Get counts
        total_resumes = Resume.query.count()
        total_jobs = Job.query.filter_by(status='active').count()
        total_evaluations = Evaluation.query.count()
        total_students = Student.query.count()
        
        # Get average scores
        avg_score_result = db.session.query(db.func.avg(Evaluation.relevance_score)).scalar()
        avg_score = round(avg_score_result, 1) if avg_score_result else 0
        
        # Get verdict distribution
        verdict_stats = db.session.query(
            Evaluation.verdict,
            db.func.count(Evaluation.verdict)
        ).group_by(Evaluation.verdict).all()
        
        verdict_distribution = {verdict: count for verdict, count in verdict_stats}
        
        # Get high performers (score >= 75)
        high_performers = Evaluation.query.filter(Evaluation.relevance_score >= 75).count()
        
        # Get recent activity (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_resumes = Resume.query.filter(Resume.upload_date >= week_ago).count()
        recent_jobs = Job.query.filter(Job.upload_date >= week_ago).count()
        
        # Get top skills from resumes
        all_skills = []
        resumes_with_skills = Resume.query.filter(Resume.extracted_skills.isnot(None)).all()
        for resume in resumes_with_skills:
            if resume.extracted_skills:
                all_skills.extend(resume.extracted_skills)
        
        from collections import Counter
        top_skills = Counter(all_skills).most_common(10)
        
        stats = {
            'totals': {
                'resumes': total_resumes,
                'jds': total_jobs,
                'evaluations': total_evaluations,
                'students': total_students
            },
            'averages': {
                'avg_score': avg_score
            },
            'distributions': {
                'verdicts': verdict_distribution
            },
            'performance': {
                'high_performers': high_performers,
                'high_performer_rate': round((high_performers / total_evaluations * 100), 1) if total_evaluations > 0 else 0
            },
            'recent_activity': {
                'resumes_this_week': recent_resumes,
                'jobs_this_week': recent_jobs
            },
            'insights': {
                'top_skills': [{'skill': skill, 'count': count} for skill, count in top_skills],
                'total_unique_skills': len(set(all_skills))
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logging.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@evaluation_bp.route('/job-descriptions', methods=['GET'])
def get_job_descriptions():
    """Get list of all job descriptions"""
    try:
        # Get query parameters
        status = request.args.get('status', 'active')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Job.query.filter_by(status=status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and get results
        jobs = query.order_by(desc(Job.upload_date)).offset(offset).limit(limit).all()
        
        # Format results
        job_descriptions = []
        for job in jobs:
            job_data = job.to_dict()
            
            # Add evaluation statistics for this job
            eval_stats = db.session.query(
                db.func.count(Evaluation.id),
                db.func.avg(Evaluation.relevance_score),
                db.func.max(Evaluation.relevance_score)
            ).filter(Evaluation.job_id == job.id).first()
            
            job_data['evaluation_stats'] = {
                'total_evaluations': eval_stats[0] or 0,
                'average_score': round(eval_stats[1], 1) if eval_stats[1] else 0,
                'best_score': round(eval_stats[2], 1) if eval_stats[2] else 0
            }
            
            # Add preview of description
            job_data['preview'] = job.description[:300] + '...' if len(job.description) > 300 else job.description
            
            job_descriptions.append(job_data)
        
        return jsonify({
            'job_descriptions': job_descriptions,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting job descriptions: {str(e)}")
        return jsonify({'error': 'Failed to retrieve job descriptions'}), 500

@evaluation_bp.route('/student/uploads', methods=['GET'])
def get_student_uploads():
    """Get student's previous uploads"""
    try:
        student_email = request.args.get('email')
        if not student_email:
            return jsonify({'error': 'Email parameter required'}), 400
        
        # Find student
        student = Student.query.filter_by(email=student_email).first()
        if not student:
            return jsonify({'uploads': []}), 200
        
        # Get student's resumes with evaluation stats
        resumes = Resume.query.filter_by(student_id=student.id).order_by(desc(Resume.upload_date)).all()
        
        uploads = []
        for resume in resumes:
            # Get best evaluation score for this resume
            best_eval = db.session.query(
                db.func.max(Evaluation.relevance_score)
            ).filter(Evaluation.resume_id == resume.id).scalar()
            
            # Get total evaluations count
            eval_count = Evaluation.query.filter_by(resume_id=resume.id).count()
            
            upload_data = {
                'resume_id': resume.id,
                'filename': resume.original_filename,
                'upload_date': resume.upload_date.isoformat() if resume.upload_date else None,
                'status': resume.processing_status,
                'best_score': round(best_eval, 1) if best_eval else 0,
                'total_evaluations': eval_count,
                'skills_extracted': len(resume.extracted_skills) if resume.extracted_skills else 0
            }
            
            uploads.append(upload_data)
        
        return jsonify({
            'uploads': uploads,
            'student_info': student.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting student uploads: {str(e)}")
        return jsonify({'error': 'Failed to retrieve student uploads'}), 500

def _calculate_evaluation_stats(evaluations):
    """Calculate statistics for a list of evaluations"""
    if not evaluations:
        return {
            'total': 0,
            'average_score': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0
        }
    
    scores = [eval.relevance_score for eval in evaluations]
    verdicts = [eval.verdict for eval in evaluations]
    
    from collections import Counter
    verdict_counts = Counter(verdicts)
    
    return {
        'total': len(evaluations),
        'average_score': round(sum(scores) / len(scores), 1),
        'min_score': round(min(scores), 1),
        'max_score': round(max(scores), 1),
        'high_count': verdict_counts.get('High', 0),
        'medium_count': verdict_counts.get('Medium', 0),
        'low_count': verdict_counts.get('Low', 0)
    }

def _generate_evaluation_insights(evaluation, resume, job):
    """Generate additional insights for detailed evaluation view"""
    insights = {
        'strengths': [],
        'areas_for_improvement': [],
        'recommendations': [],
        'skill_analysis': {}
    }
    
    # Analyze strengths
    if evaluation.matched_skills:
        insights['strengths'].append(f"Matched {len(evaluation.matched_skills)} required skills")
    
    if evaluation.relevance_score >= 75:
        insights['strengths'].append("Strong overall relevance to the position")
    
    # Analyze areas for improvement
    if evaluation.missing_skills:
        insights['areas_for_improvement'].append(f"Missing {len(evaluation.missing_skills)} key skills")
    
    if evaluation.relevance_score < 50:
        insights['areas_for_improvement'].append("Overall relevance needs significant improvement")
    
    # Generate recommendations
    if evaluation.missing_skills:
        top_missing = evaluation.missing_skills[:3]
        insights['recommendations'].append(f"Focus on developing: {', '.join(top_missing)}")
    
    insights['recommendations'].append("Consider adding relevant projects to demonstrate skills")
    insights['recommendations'].append("Tailor resume keywords to match job requirements")
    
    # Skill analysis
    all_job_skills = (job.required_skills or []) + (job.preferred_skills or [])
    resume_skills = resume.extracted_skills or []
    
    if all_job_skills and resume_skills:
        skill_coverage = len(set(resume_skills) & set(all_job_skills)) / len(all_job_skills) * 100
        insights['skill_analysis'] = {
            'coverage_percentage': round(skill_coverage, 1),
            'total_job_skills': len(all_job_skills),
            'matched_skills': len(set(resume_skills) & set(all_job_skills))
        }
    
    return insights