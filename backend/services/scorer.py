from typing import Dict, Tuple
import logging
from config import Config

class RelevanceScorer:
    def __init__(self):
        self.semantic_weight = getattr(Config, 'SEMANTIC_WEIGHT', 0.6)
        self.keyword_weight = getattr(Config, 'KEYWORD_WEIGHT', 0.4)
        self.high_threshold = getattr(Config, 'HIGH_RELEVANCE_THRESHOLD', 75)
        self.medium_threshold = getattr(Config, 'MEDIUM_RELEVANCE_THRESHOLD', 50)
    
    def calculate_keyword_score(self, match_results: Dict) -> float:
        """Calculate keyword-based score"""
        try:
            # Get scores from different matching techniques
            exact_skill_score = match_results.get('exact_skill_match', {}).get('match_percentage', 0)
            fuzzy_skill_score = match_results.get('fuzzy_skill_match', {}).get('fuzzy_match_percentage', 0)
            bm25_score = match_results.get('bm25_match', {}).get('normalized_score', 0)
            
            # Weighted combination of keyword scores
            keyword_score = (
                exact_skill_score * 0.5 +  # 50% weight to exact skill matches
                fuzzy_skill_score * 0.3 +  # 30% weight to fuzzy skill matches
                bm25_score * 0.2           # 20% weight to BM25 keyword matching
            )
            
            return min(keyword_score, 100.0)  # Cap at 100
            
        except Exception as e:
            logging.error(f"Error calculating keyword score: {str(e)}")
            return 0.0
    
    def calculate_semantic_score(self, match_results: Dict, embedding_similarity: float = None) -> float:
        """Calculate semantic similarity score"""
        try:
            # Get TF-IDF similarity
            tfidf_score = match_results.get('tfidf_match', {}).get('similarity_percentage', 0)
            
            # If we have embedding similarity from LLM, use it
            if embedding_similarity is not None:
                # Combine TF-IDF and embedding similarity
                semantic_score = (tfidf_score * 0.4 + embedding_similarity * 0.6)
            else:
                # Use only TF-IDF if no embedding similarity available
                semantic_score = tfidf_score
            
            return min(semantic_score, 100.0)  # Cap at 100
            
        except Exception as e:
            logging.error(f"Error calculating semantic score: {str(e)}")
            return 0.0
    
    def calculate_weighted_score(self, keyword_score: float, semantic_score: float) -> float:
        """Calculate final weighted relevance score"""
        try:
            weighted_score = (
                semantic_score * self.semantic_weight +
                keyword_score * self.keyword_weight
            )
            
            return min(weighted_score, 100.0)  # Cap at 100
            
        except Exception as e:
            logging.error(f"Error calculating weighted score: {str(e)}")
            return 0.0
    
    def calculate_bonus_scores(self, match_results: Dict) -> float:
        """Calculate bonus scores for additional factors"""
        bonus_score = 0.0
        
        try:
            # Experience bonus
            experience_match = match_results.get('experience_match', {})
            if experience_match.get('has_experience', False):
                bonus_score += 5.0  # 5 points for having experience
            
            # Education bonus
            education_match = match_results.get('education_match', {})
            if education_match.get('has_degree', False):
                bonus_score += 3.0  # 3 points for having degree
            
            # High skill match bonus
            exact_match = match_results.get('exact_skill_match', {})
            if exact_match.get('match_percentage', 0) > 80:
                bonus_score += 7.0  # 7 points for high skill match
            
            return min(bonus_score, 15.0)  # Cap bonus at 15 points
            
        except Exception as e:
            logging.error(f"Error calculating bonus scores: {str(e)}")
            return 0.0
    
    def determine_verdict(self, final_score: float) -> str:
        """Determine verdict based on score"""
        if final_score >= self.high_threshold:
            return "High"
        elif final_score >= self.medium_threshold:
            return "Medium"
        else:
            return "Low"
    
    def calculate_comprehensive_score(self, match_results: Dict, embedding_similarity: float = None) -> Dict:
        """Calculate comprehensive relevance score"""
        try:
            # Calculate individual scores
            keyword_score = self.calculate_keyword_score(match_results)
            semantic_score = self.calculate_semantic_score(match_results, embedding_similarity)
            bonus_score = self.calculate_bonus_scores(match_results)
            
            # Calculate weighted score
            base_weighted_score = self.calculate_weighted_score(keyword_score, semantic_score)
            
            # Add bonus score
            final_score = min(base_weighted_score + bonus_score, 100.0)
            
            # Determine verdict
            verdict = self.determine_verdict(final_score)
            
            # Prepare detailed scoring breakdown
            scoring_details = {
                'final_score': round(final_score, 2),
                'verdict': verdict,
                'score_breakdown': {
                    'keyword_score': round(keyword_score, 2),
                    'semantic_score': round(semantic_score, 2),
                    'base_weighted_score': round(base_weighted_score, 2),
                    'bonus_score': round(bonus_score, 2),
                    'weights_used': {
                        'semantic_weight': self.semantic_weight,
                        'keyword_weight': self.keyword_weight
                    }
                },
                'thresholds': {
                    'high_threshold': self.high_threshold,
                    'medium_threshold': self.medium_threshold
                }
            }
            
            return scoring_details
            
        except Exception as e:
            logging.error(f"Error in comprehensive scoring: {str(e)}")
            return {
                'final_score': 0.0,
                'verdict': 'Low',
                'error': str(e)
            }
    
    def generate_missing_elements(self, match_results: Dict) -> Dict:
        """Generate list of missing elements from job requirements"""
        try:
            missing_elements = {}
            
            # Missing skills
            exact_match = match_results.get('exact_skill_match', {})
            fuzzy_match = match_results.get('fuzzy_skill_match', {})
            
            missing_skills = exact_match.get('missing_skills', [])
            missing_elements['skills'] = missing_skills[:10]  # Top 10 missing skills
            
            # Missing certifications (placeholder - would need more sophisticated analysis)
            missing_elements['certifications'] = [
                'AWS Certification',
                'Google Cloud Certification',
                'Project Management Certification'
            ][:3]  # Sample missing certifications
            
            # Missing projects (placeholder - would need job description analysis)
            missing_elements['projects'] = [
                'End-to-end web application project',
                'Machine learning project with real data',
                'Mobile application development'
            ][:3]  # Sample missing projects
            
            # Missing experience areas
            missing_elements['experience'] = [
                'Industry-specific experience',
                'Leadership experience',
                'Team collaboration experience'
            ][:3]  # Sample missing experience
            
            return missing_elements
            
        except Exception as e:
            logging.error(f"Error generating missing elements: {str(e)}")
            return {
                'skills': [],
                'certifications': [],
                'projects': [],
                'experience': []
            }
    
    def generate_skill_gap_analysis(self, match_results: Dict) -> Dict:
        """Generate detailed skill gap analysis"""
        try:
            skill_analysis = {}
            
            # Matched skills analysis
            exact_match = match_results.get('exact_skill_match', {})
            fuzzy_match = match_results.get('fuzzy_skill_match', {})
            
            skill_analysis['matched_skills'] = exact_match.get('matched_skills', [])
            skill_analysis['partially_matched_skills'] = [
                match['job_skill'] for match in fuzzy_match.get('matched_skills', [])
                if match['similarity'] < 90  # Partial matches
            ]
            
            skill_analysis['missing_critical_skills'] = exact_match.get('missing_skills', [])[:5]
            skill_analysis['skill_match_percentage'] = exact_match.get('match_percentage', 0)
            
            # Skill importance ranking (placeholder - would need job analysis)
            skill_analysis['skill_importance'] = {
                skill: 'High' if i < 3 else 'Medium' if i < 6 else 'Low'
                for i, skill in enumerate(exact_match.get('missing_skills', [])[:10])
            }
            
            return skill_analysis
            
        except Exception as e:
            logging.error(f"Error in skill gap analysis: {str(e)}")
            return {}