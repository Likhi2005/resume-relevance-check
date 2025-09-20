import os
from typing import Dict, List
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import json

class FeedbackGenerator:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    google_api_key=self.api_key,
                    temperature=0.3
                )
            except Exception as e:
                logging.warning(f"Could not initialize Gemini: {str(e)}")
                self.llm = None
        else:
            logging.warning("GOOGLE_API_KEY not found. LLM feedback will be disabled.")
            self.llm = None
    
    def generate_personalized_feedback(self, resume_data: Dict, job_data: Dict, 
                                     scoring_results: Dict, match_results: Dict) -> str:
        """Generate personalized improvement feedback using LLM"""
        if not self.llm:
            return self._generate_fallback_feedback(scoring_results, match_results)
        
        try:
            # Prepare context for LLM
            context = self._prepare_feedback_context(resume_data, job_data, scoring_results, match_results)
            
            # Create prompt
            prompt = self._create_feedback_prompt(context)
            
            # Generate feedback
            response = self.llm.invoke([HumanMessage(content=prompt)])
            feedback = response.content.strip()
            
            return feedback
            
        except Exception as e:
            logging.error(f"Error generating LLM feedback: {str(e)}")
            return self._generate_fallback_feedback(scoring_results, match_results)
    
    def _prepare_feedback_context(self, resume_data: Dict, job_data: Dict, 
                                scoring_results: Dict, match_results: Dict) -> Dict:
        """Prepare context for feedback generation"""
        context = {
            'job_title': job_data.get('title', 'Position'),
            'company': job_data.get('company', 'Company'),
            'relevance_score': scoring_results.get('final_score', 0),
            'verdict': scoring_results.get('verdict', 'Low'),
            'matched_skills': match_results.get('exact_skill_match', {}).get('matched_skills', []),
            'missing_skills': match_results.get('exact_skill_match', {}).get('missing_skills', []),
            'resume_skills': resume_data.get('skills', []),
            'job_required_skills': job_data.get('required_skills', []),
            'job_preferred_skills': job_data.get('preferred_skills', []),
            'has_experience': match_results.get('experience_match', {}).get('has_experience', False),
            'has_degree': match_results.get('education_match', {}).get('has_degree', False),
            'keyword_score': scoring_results.get('score_breakdown', {}).get('keyword_score', 0),
            'semantic_score': scoring_results.get('score_breakdown', {}).get('semantic_score', 0)
        }
        return context
    
    def _create_feedback_prompt(self, context: Dict) -> str:
        """Create detailed prompt for feedback generation"""
        prompt = f"""
You are a career counselor helping a student improve their resume for job applications.

Job Details:
- Position: {context['job_title']} at {context['company']}
- Required Skills: {', '.join(context['job_required_skills'][:10])}
- Preferred Skills: {', '.join(context['job_preferred_skills'][:5])}

Student's Resume Analysis:
- Overall Relevance Score: {context['relevance_score']:.1f}/100
- Verdict: {context['verdict']} suitability
- Current Skills: {', '.join(context['resume_skills'][:10])}
- Matched Skills: {', '.join(context['matched_skills'][:5])}
- Missing Skills: {', '.join(context['missing_skills'][:5])}
- Has Work Experience: {context['has_experience']}
- Has Degree: {context['has_degree']}

Task: Provide personalized, actionable feedback to help this student improve their resume for this specific job. 

Your feedback should:
1. Acknowledge their strengths
2. Identify the most critical gaps
3. Provide specific, actionable recommendations
4. Suggest learning resources or projects
5. Be encouraging and constructive

Focus on the top 3-5 most impactful improvements. Keep the response between 150-250 words.

Personalized Feedback:
"""
        return prompt
    
    def _generate_fallback_feedback(self, scoring_results: Dict, match_results: Dict) -> str:
        """Generate rule-based feedback when LLM is not available"""
        score = scoring_results.get('final_score', 0)
        verdict = scoring_results.get('verdict', 'Low')
        missing_skills = match_results.get('exact_skill_match', {}).get('missing_skills', [])
        matched_skills = match_results.get('exact_skill_match', {}).get('matched_skills', [])
        
        if score >= 75:
            feedback = f"Excellent match! Your resume shows strong alignment with the job requirements. "
            feedback += f"You have {len(matched_skills)} key skills that match perfectly. "
            if missing_skills:
                feedback += f"To further strengthen your profile, consider gaining experience in: {', '.join(missing_skills[:3])}."
        
        elif score >= 50:
            feedback = f"Good foundation! Your resume has moderate alignment with the job requirements. "
            feedback += f"You match {len(matched_skills)} key skills. "
            feedback += f"Focus on developing these critical skills: {', '.join(missing_skills[:5])}. "
            feedback += "Consider adding relevant projects or certifications in these areas."
        
        else:
            feedback = f"Significant gaps identified. Your resume needs substantial improvements for this role. "
            feedback += f"Priority skills to develop: {', '.join(missing_skills[:5])}. "
            feedback += "Consider taking online courses, building projects, or gaining certifications in these areas. "
            feedback += "Focus on the most in-demand skills first."
        
        return feedback
    
    def generate_improvement_suggestions(self, missing_elements: Dict, 
                                       job_data: Dict) -> List[Dict]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Skill-based suggestions
        missing_skills = missing_elements.get('skills', [])
        for skill in missing_skills[:5]:
            suggestions.append({
                'type': 'skill',
                'priority': 'High' if skill.lower() in ['python', 'javascript', 'sql', 'react', 'java'] else 'Medium',
                'suggestion': f"Learn {skill}",
                'action': f"Take an online course or build a project using {skill}",
                'resources': self._get_learning_resources(skill)
            })
        
        # Project-based suggestions
        if missing_elements.get('projects'):
            suggestions.append({
                'type': 'project',
                'priority': 'High',
                'suggestion': "Build relevant projects",
                'action': "Create 2-3 projects that demonstrate the required skills",
                'resources': ["GitHub", "Personal Portfolio", "Kaggle (for data science)"]
            })
        
        # Certification suggestions
        if missing_elements.get('certifications'):
            suggestions.append({
                'type': 'certification',
                'priority': 'Medium',
                'suggestion': "Obtain relevant certifications",
                'action': "Get certified in cloud platforms or technologies mentioned in the job",
                'resources': ["Coursera", "AWS Training", "Google Cloud Training"]
            })
        
        return suggestions[:8]  # Return top 8 suggestions
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """Get learning resources for specific skills"""
        skill_lower = skill.lower()
        
        resource_map = {
            'python': ['Python.org Tutorial', 'Codecademy Python', 'Real Python'],
            'javascript': ['MDN Web Docs', 'freeCodeCamp', 'JavaScript.info'],
            'react': ['React Official Docs', 'React Tutorial', 'Create React App'],
            'sql': ['W3Schools SQL', 'SQLBolt', 'MySQL Tutorial'],
            'aws': ['AWS Training', 'A Cloud Guru', 'AWS Documentation'],
            'docker': ['Docker Official Tutorial', 'Docker Hub', 'Play with Docker'],
            'git': ['Git Tutorial', 'GitHub Learning Lab', 'Atlassian Git Tutorials']
        }
        
        return resource_map.get(skill_lower, ['Google Search', 'YouTube Tutorials', 'Online Courses'])
    
    def generate_skill_roadmap(self, current_skills: List[str], 
                             target_skills: List[str]) -> Dict:
        """Generate a learning roadmap for skill development"""
        roadmap = {
            'current_level': 'Beginner' if len(current_skills) < 5 else 'Intermediate',
            'target_level': 'Job-ready',
            'timeline': '3-6 months',
            'phases': []
        }
        
        # Phase 1: Foundation skills
        foundation_skills = [skill for skill in target_skills 
                           if skill.lower() in ['python', 'java', 'javascript', 'html', 'css']]
        if foundation_skills:
            roadmap['phases'].append({
                'phase': 1,
                'title': 'Foundation Skills',
                'duration': '4-6 weeks',
                'skills': foundation_skills[:3],
                'goals': 'Build strong programming fundamentals'
            })
        
        # Phase 2: Advanced skills
        advanced_skills = [skill for skill in target_skills 
                         if skill.lower() in ['react', 'angular', 'vue', 'nodejs', 'django']]
        if advanced_skills:
            roadmap['phases'].append({
                'phase': 2,
                'title': 'Framework & Libraries',
                'duration': '6-8 weeks',
                'skills': advanced_skills[:3],
                'goals': 'Learn popular frameworks and libraries'
            })
        
        # Phase 3: Specialized skills
        specialized_skills = [skill for skill in target_skills 
                            if skill.lower() in ['aws', 'docker', 'kubernetes', 'tensorflow']]
        if specialized_skills:
            roadmap['phases'].append({
                'phase': 3,
                'title': 'Specialized Technologies',
                'duration': '4-6 weeks',
                'skills': specialized_skills[:3],
                'goals': 'Master industry-specific tools'
            })
        
        return roadmap