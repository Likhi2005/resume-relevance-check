import re
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from rank_bm25 import BM25Okapi
import numpy as np
import logging

class ResumeJobMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            lowercase=True
        )
        
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for matching"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def exact_skill_match(self, resume_skills: List[str], job_skills: List[str]) -> Dict:
        """Perform exact skill matching"""
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills_lower:
            if job_skill in resume_skills_lower:
                matched_skills.append(job_skill)
            else:
                missing_skills.append(job_skill)
        
        match_percentage = (len(matched_skills) / len(job_skills_lower)) * 100 if job_skills_lower else 0
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_percentage': match_percentage,
            'matched_count': len(matched_skills),
            'total_required': len(job_skills_lower)
        }
    
    def fuzzy_skill_match(self, resume_skills: List[str], job_skills: List[str], threshold: int = 80) -> Dict:
        """Perform fuzzy skill matching"""
        matched_skills = []
        missing_skills = []
        skill_similarities = {}
        
        for job_skill in job_skills:
            best_match = None
            best_score = 0
            
            for resume_skill in resume_skills:
                # Use different fuzzy matching ratios
                ratio = fuzz.ratio(job_skill.lower(), resume_skill.lower())
                partial_ratio = fuzz.partial_ratio(job_skill.lower(), resume_skill.lower())
                token_ratio = fuzz.token_sort_ratio(job_skill.lower(), resume_skill.lower())
                
                # Take the maximum score
                score = max(ratio, partial_ratio, token_ratio)
                
                if score > best_score:
                    best_score = score
                    best_match = resume_skill
            
            if best_score >= threshold:
                matched_skills.append({
                    'job_skill': job_skill,
                    'resume_skill': best_match,
                    'similarity': best_score
                })
                skill_similarities[job_skill] = best_score
            else:
                missing_skills.append(job_skill)
        
        fuzzy_match_percentage = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skill_similarities': skill_similarities,
            'fuzzy_match_percentage': fuzzy_match_percentage,
            'threshold_used': threshold
        }
    
    def keyword_match_bm25(self, resume_text: str, job_text: str) -> Dict:
        """Perform BM25 keyword matching"""
        try:
            # Preprocess texts
            resume_words = self.preprocess_text(resume_text)
            job_words = self.preprocess_text(job_text)
            
            # Create corpus
            corpus = [resume_words, job_words]
            
            # Initialize BM25
            bm25 = BM25Okapi(corpus)
            
            # Score resume against job description
            job_score = bm25.get_scores(job_words)[0]  # Score of resume against job query
            
            # Get top matching terms
            job_word_scores = [(word, bm25.get_scores([word])[0]) for word in set(job_words)]
            job_word_scores.sort(key=lambda x: x[1], reverse=True)
            
            return {
                'bm25_score': float(job_score),
                'top_matching_terms': job_word_scores[:10],
                'normalized_score': min(job_score / 10, 1.0) * 100  # Normalize to 0-100
            }
            
        except Exception as e:
            logging.error(f"Error in BM25 matching: {str(e)}")
            return {
                'bm25_score': 0.0,
                'top_matching_terms': [],
                'normalized_score': 0.0
            }
    
    def tfidf_similarity(self, resume_text: str, job_text: str) -> Dict:
        """Calculate TF-IDF cosine similarity"""
        try:
            # Fit TF-IDF on both texts
            corpus = [resume_text, job_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            similarity_score = similarity_matrix[0][1]  # Similarity between resume and job
            
            # Get feature names and their importance
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()
            
            # Get top features for job description
            job_features = tfidf_scores[1]
            top_features_idx = job_features.argsort()[-20:][::-1]  # Top 20 features
            top_features = [(feature_names[idx], job_features[idx]) for idx in top_features_idx if job_features[idx] > 0]
            
            return {
                'tfidf_similarity': float(similarity_score),
                'similarity_percentage': float(similarity_score * 100),
                'top_job_features': top_features,
                'resume_vector_size': tfidf_scores[0].shape[0],
                'job_vector_size': tfidf_scores[1].shape[0]
            }
            
        except Exception as e:
            logging.error(f"Error in TF-IDF similarity: {str(e)}")
            return {
                'tfidf_similarity': 0.0,
                'similarity_percentage': 0.0,
                'top_job_features': [],
                'resume_vector_size': 0,
                'job_vector_size': 0
            }
    
    def comprehensive_match(self, resume_data: Dict, job_data: Dict) -> Dict:
        """Perform comprehensive matching using multiple techniques"""
        try:
            # Extract relevant data
            resume_skills = resume_data.get('skills', [])
            job_required_skills = job_data.get('required_skills', [])
            job_preferred_skills = job_data.get('preferred_skills', [])
            
            resume_text = resume_data.get('clean_text', '')
            job_text = job_data.get('clean_text', '')
            
            # Perform different types of matching
            exact_match = self.exact_skill_match(resume_skills, job_required_skills)
            fuzzy_match = self.fuzzy_skill_match(resume_skills, job_required_skills + job_preferred_skills)
            bm25_match = self.keyword_match_bm25(resume_text, job_text)
            tfidf_match = self.tfidf_similarity(resume_text, job_text)
            
            # Calculate additional metrics
            experience_match = self._match_experience(resume_data, job_data)
            education_match = self._match_education(resume_data, job_data)
            
            return {
                'exact_skill_match': exact_match,
                'fuzzy_skill_match': fuzzy_match,
                'bm25_match': bm25_match,
                'tfidf_match': tfidf_match,
                'experience_match': experience_match,
                'education_match': education_match,
                'overall_metrics': {
                    'skills_covered': exact_match['match_percentage'],
                    'text_similarity': tfidf_match['similarity_percentage'],
                    'keyword_relevance': bm25_match['normalized_score']
                }
            }
            
        except Exception as e:
            logging.error(f"Error in comprehensive matching: {str(e)}")
            return {'error': str(e)}
    
    def _match_experience(self, resume_data: Dict, job_data: Dict) -> Dict:
        """Match experience requirements"""
        resume_exp = resume_data.get('experience', [])
        job_exp_req = job_data.get('experience_requirements', [])
        
        # Extract years of experience
        resume_years = []
        for exp in resume_exp:
            if isinstance(exp, dict) and 'years' in exp:
                try:
                    years = int(exp['years'])
                    resume_years.append(years)
                except (ValueError, TypeError):
                    continue
        
        max_resume_years = max(resume_years) if resume_years else 0
        
        # Simple experience matching (can be enhanced)
        return {
            'resume_max_years': max_resume_years,
            'has_experience': len(resume_exp) > 0,
            'experience_details': resume_exp[:3]  # Top 3 experiences
        }
    
    def _match_education(self, resume_data: Dict, job_data: Dict) -> Dict:
        """Match education requirements"""
        resume_edu = resume_data.get('education', [])
        job_edu_req = job_data.get('education_requirements', [])
        
        # Simple education matching
        has_degree = len(resume_edu) > 0
        education_types = [edu.get('degree', '') for edu in resume_edu if isinstance(edu, dict)]
        
        return {
            'has_degree': has_degree,
            'education_types': education_types,
            'education_details': resume_edu
        }