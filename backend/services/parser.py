import fitz  # PyMuPDF
import docx
import docx2txt
import re
import spacy
from typing import Dict, List, Optional
import logging

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy model 'en_core_web_sm' not found. Install it with: python -m spacy download en_core_web_sm")
    nlp = None

class DocumentParser:
    def __init__(self):
        self.skills_keywords = [
            'python', 'java', 'javascript', 'react', 'nodejs', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'html', 'css', 'angular',
            'vue', 'django', 'flask', 'fastapi', 'postgresql', 'mysql',
            'redis', 'elasticsearch', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'opencv', 'nlp',
            'machine learning', 'deep learning', 'data science', 'artificial intelligence'
        ]
        
        self.education_patterns = [
            r'b\.?tech|bachelor of technology|btech',
            r'm\.?tech|master of technology|mtech',
            r'b\.?e\.?|bachelor of engineering',
            r'm\.?e\.?|master of engineering',
            r'b\.?sc|bachelor of science',
            r'm\.?sc|master of science',
            r'mca|master of computer applications',
            r'bca|bachelor of computer applications',
            r'phd|doctorate'
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            # Try with python-docx first
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # If empty, try with docx2txt
            if not text.strip():
                text = docx2txt.process(file_path)
            
            return text
        except Exception as e:
            logging.error(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from file based on extension"""
        if file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(('.docx', '.doc')):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep alphanumeric and common punctuation
        text = re.sub(r'[^\w\s\.\,\-\+\#\(\)\/]', ' ', text)
        return text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Use spaCy for additional entity extraction if available
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT'] and len(ent.text) > 2:
                    # Filter for technology-related entities
                    if any(tech_word in ent.text.lower() for tech_word in ['tech', 'soft', 'system', 'platform']):
                        found_skills.append(ent.text)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        text_lower = text.lower()
        
        for pattern in self.education_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context for more details
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                education.append({
                    'degree': match.group(),
                    'context': context.strip()
                })
        
        return education
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        # Look for common experience patterns
        experience_patterns = [
            r'(\d+)\s*(years?|yrs?)\s*(of\s*)?(experience|exp)',
            r'(experience|exp)\s*:?\s*(\d+)\s*(years?|yrs?)',
            r'(\d+)\+?\s*(years?|yrs?)'
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                experience.append({
                    'text': match.group(),
                    'years': re.findall(r'\d+', match.group())[0] if re.findall(r'\d+', match.group()) else None
                })
        
        # Extract job titles and companies using spaCy if available
        if nlp:
            doc = nlp(text)
            organizations = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
            if organizations:
                experience.extend([{'company': org} for org in organizations[:5]])  # Top 5
        
        return experience
    
    def extract_projects(self, text: str) -> List[str]:
        """Extract project information"""
        projects = []
        
        # Look for sections that might contain projects
        project_sections = re.finditer(r'(projects?|portfolio|work samples?)[\s\:]*([^\n]*(?:\n(?!\s*\n)[^\n]*)*)', 
                                     text, re.IGNORECASE | re.MULTILINE)
        
        for section in project_sections:
            project_text = section.group(2)
            # Split by common delimiters
            project_lines = re.split(r'[\n\•\-\*]', project_text)
            for line in project_lines:
                line = line.strip()
                if len(line) > 10:  # Filter out very short lines
                    projects.append(line)
        
        return projects[:10]  # Limit to 10 projects
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certification information"""
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'certified?\s+[\w\s]+',
            r'[\w\s]*\s*certification',
            r'aws\s+[\w\s]*',
            r'google\s+[\w\s]*certified',
            r'microsoft\s+[\w\s]*certified',
            r'cisco\s+[\w\s]*',
            r'oracle\s+[\w\s]*certified'
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                cert_text = match.group().strip()
                if len(cert_text) > 5:
                    certifications.append(cert_text)
        
        return list(set(certifications))  # Remove duplicates
    
    def parse_resume(self, file_path: str) -> Dict:
        """Parse resume and extract all information"""
        try:
            # Extract raw text
            raw_text = self.extract_text(file_path)
            if not raw_text:
                return {'error': 'Could not extract text from file'}
            
            # Clean text
            clean_text = self.clean_text(raw_text)
            
            # Extract structured information
            parsed_data = {
                'raw_text': raw_text,
                'clean_text': clean_text,
                'skills': self.extract_skills(clean_text),
                'education': self.extract_education(clean_text),
                'experience': self.extract_experience(clean_text),
                'projects': self.extract_projects(clean_text),
                'certifications': self.extract_certifications(clean_text)
            }
            
            return parsed_data
            
        except Exception as e:
            logging.error(f"Error parsing resume: {str(e)}")
            return {'error': str(e)}
    
    def parse_job_description(self, text: str) -> Dict:
        """Parse job description and extract requirements"""
        try:
            clean_text = self.clean_text(text)
            
            # Extract job requirements
            parsed_data = {
                'raw_text': text,
                'clean_text': clean_text,
                'required_skills': self.extract_skills(clean_text),
                'education_requirements': self.extract_education(clean_text),
                'experience_requirements': self.extract_experience(clean_text),
                'certifications': self.extract_certifications(clean_text)
            }
            
            # Extract specific sections if present
            sections = {
                'responsibilities': self._extract_section(clean_text, ['responsibilities', 'duties', 'role']),
                'requirements': self._extract_section(clean_text, ['requirements', 'qualifications', 'must have']),
                'preferred': self._extract_section(clean_text, ['preferred', 'nice to have', 'bonus'])
            }
            
            parsed_data.update(sections)
            return parsed_data
            
        except Exception as e:
            logging.error(f"Error parsing job description: {str(e)}")
            return {'error': str(e)}
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract specific sections from text based on keywords"""
        for keyword in keywords:
            pattern = rf'{keyword}[\s\:]*([^\n]*(?:\n(?!\s*\n)[^\n]*)*)'
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return ""