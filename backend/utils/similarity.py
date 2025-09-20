import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re
import logging

class SimilarityCalculator:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            lowercase=True,
            min_df=1,
            max_df=0.95
        )
        
        self.count_vectorizer = CountVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            lowercase=True
        )
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for similarity calculation"""
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Convert to lowercase
        text = text.lower().strip()
        return text
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words"""
        preprocessed = self.preprocess_text(text)
        return preprocessed.split()
    
    def calculate_tfidf_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate TF-IDF cosine similarity between two texts"""
        try:
            # Preprocess texts
            processed_text1 = self.preprocess_text(text1)
            processed_text2 = self.preprocess_text(text2)
            
            # Create corpus
            corpus = [processed_text1, processed_text2]
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            similarity_score = similarity_matrix[0][1]
            
            # Get feature importance
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()
            
            # Get top features for each text
            text1_features = self._get_top_features(tfidf_scores[0], feature_names, top_n=10)
            text2_features = self._get_top_features(tfidf_scores[1], feature_names, top_n=10)
            
            return {
                'similarity_score': float(similarity_score),
                'similarity_percentage': float(similarity_score * 100),
                'text1_top_features': text1_features,
                'text2_top_features': text2_features,
                'method': 'tfidf_cosine'
            }
            
        except Exception as e:
            logging.error(f"Error calculating TF-IDF similarity: {str(e)}")
            return {
                'similarity_score': 0.0,
                'similarity_percentage': 0.0,
                'error': str(e)
            }
    
    def calculate_bm25_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate BM25 similarity between two texts"""
        try:
            # Tokenize texts
            tokens1 = self.tokenize_text(text1)
            tokens2 = self.tokenize_text(text2)
            
            # Create corpus
            corpus = [tokens1, tokens2]
            
            # Initialize BM25
            bm25 = BM25Okapi(corpus)
            
            # Calculate scores
            score1_vs_2 = bm25.get_scores(tokens2)[0]  # How well text1 matches text2 query
            score2_vs_1 = bm25.get_scores(tokens1)[1]  # How well text2 matches text1 query
            
            # Average the scores for bidirectional similarity
            avg_score = (score1_vs_2 + score2_vs_1) / 2
            
            # Normalize score (BM25 scores can vary widely)
            normalized_score = min(avg_score / 10, 1.0)  # Normalize to 0-1 range
            
            return {
                'bm25_score': float(avg_score),
                'normalized_score': float(normalized_score),
                'similarity_percentage': float(normalized_score * 100),
                'score1_vs_2': float(score1_vs_2),
                'score2_vs_1': float(score2_vs_1),
                'method': 'bm25'
            }
            
        except Exception as e:
            logging.error(f"Error calculating BM25 similarity: {str(e)}")
            return {
                'bm25_score': 0.0,
                'normalized_score': 0.0,
                'similarity_percentage': 0.0,
                'error': str(e)
            }
    
    def calculate_jaccard_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate Jaccard similarity between two texts"""
        try:
            # Tokenize texts into sets
            tokens1 = set(self.tokenize_text(text1))
            tokens2 = set(self.tokenize_text(text2))
            
            # Calculate Jaccard similarity
            intersection = len(tokens1.intersection(tokens2))
            union = len(tokens1.union(tokens2))
            
            jaccard_score = intersection / union if union > 0 else 0.0
            
            # Find common and unique tokens
            common_tokens = list(tokens1.intersection(tokens2))
            unique_to_text1 = list(tokens1 - tokens2)
            unique_to_text2 = list(tokens2 - tokens1)
            
            return {
                'jaccard_score': float(jaccard_score),
                'similarity_percentage': float(jaccard_score * 100),
                'intersection_size': intersection,
                'union_size': union,
                'common_tokens': common_tokens[:20],  # Top 20 common tokens
                'unique_to_text1': unique_to_text1[:10],  # Top 10 unique to text1
                'unique_to_text2': unique_to_text2[:10],  # Top 10 unique to text2
                'method': 'jaccard'
            }
            
        except Exception as e:
            logging.error(f"Error calculating Jaccard similarity: {str(e)}")
            return {
                'jaccard_score': 0.0,
                'similarity_percentage': 0.0,
                'error': str(e)
            }
    
    def calculate_word_overlap(self, text1: str, text2: str) -> Dict:
        """Calculate word overlap metrics between two texts"""
        try:
            tokens1 = self.tokenize_text(text1)
            tokens2 = self.tokenize_text(text2)
            
            # Convert to sets for overlap calculation
            set1 = set(tokens1)
            set2 = set(tokens2)
            
            # Calculate overlaps
            overlap = len(set1.intersection(set2))
            overlap_ratio_1 = overlap / len(set1) if len(set1) > 0 else 0.0
            overlap_ratio_2 = overlap / len(set2) if len(set2) > 0 else 0.0
            
            # Average overlap ratio
            avg_overlap_ratio = (overlap_ratio_1 + overlap_ratio_2) / 2
            
            return {
                'word_overlap_count': overlap,
                'overlap_ratio_text1': float(overlap_ratio_1),
                'overlap_ratio_text2': float(overlap_ratio_2),
                'average_overlap_ratio': float(avg_overlap_ratio),
                'similarity_percentage': float(avg_overlap_ratio * 100),
                'text1_unique_words': len(set1) - overlap,
                'text2_unique_words': len(set2) - overlap,
                'method': 'word_overlap'
            }
            
        except Exception as e:
            logging.error(f"Error calculating word overlap: {str(e)}")
            return {
                'word_overlap_count': 0,
                'similarity_percentage': 0.0,
                'error': str(e)
            }
    
    def calculate_comprehensive_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate multiple similarity metrics and return comprehensive results"""
        try:
            # Calculate different similarity metrics
            tfidf_result = self.calculate_tfidf_similarity(text1, text2)
            bm25_result = self.calculate_bm25_similarity(text1, text2)
            jaccard_result = self.calculate_jaccard_similarity(text1, text2)
            overlap_result = self.calculate_word_overlap(text1, text2)
            
            # Calculate weighted average similarity
            similarities = [
                tfidf_result.get('similarity_percentage', 0) * 0.4,  # 40% weight to TF-IDF
                bm25_result.get('similarity_percentage', 0) * 0.3,   # 30% weight to BM25
                jaccard_result.get('similarity_percentage', 0) * 0.2, # 20% weight to Jaccard
                overlap_result.get('similarity_percentage', 0) * 0.1  # 10% weight to overlap
            ]
            
            weighted_similarity = sum(similarities)
            
            return {
                'comprehensive_similarity': {
                    'weighted_average': float(weighted_similarity),
                    'individual_scores': {
                        'tfidf': tfidf_result.get('similarity_percentage', 0),
                        'bm25': bm25_result.get('similarity_percentage', 0),
                        'jaccard': jaccard_result.get('similarity_percentage', 0),
                        'word_overlap': overlap_result.get('similarity_percentage', 0)
                    }
                },
                'detailed_results': {
                    'tfidf': tfidf_result,
                    'bm25': bm25_result,
                    'jaccard': jaccard_result,
                    'word_overlap': overlap_result
                },
                'text_statistics': {
                    'text1_word_count': len(self.tokenize_text(text1)),
                    'text2_word_count': len(self.tokenize_text(text2)),
                    'text1_unique_words': len(set(self.tokenize_text(text1))),
                    'text2_unique_words': len(set(self.tokenize_text(text2)))
                }
            }
            
        except Exception as e:
            logging.error(f"Error calculating comprehensive similarity: {str(e)}")
            return {
                'comprehensive_similarity': {'weighted_average': 0.0},
                'error': str(e)
            }
    
    def _get_top_features(self, tfidf_scores: np.ndarray, feature_names: np.ndarray, 
                         top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top N features from TF-IDF scores"""
        try:
            # Get indices of top features
            top_indices = tfidf_scores.argsort()[-top_n:][::-1]
            
            # Get feature names and scores
            top_features = []
            for idx in top_indices:
                if tfidf_scores[idx] > 0:  # Only include features with positive scores
                    top_features.append((feature_names[idx], float(tfidf_scores[idx])))
            
            return top_features
            
        except Exception as e:
            logging.error(f"Error getting top features: {str(e)}")
            return []
    
    def find_key_differences(self, text1: str, text2: str) -> Dict:
        """Find key differences between two texts"""
        try:
            tokens1 = set(self.tokenize_text(text1))
            tokens2 = set(self.tokenize_text(text2))
            
            # Find differences
            only_in_text1 = list(tokens1 - tokens2)
            only_in_text2 = list(tokens2 - tokens1)
            common_tokens = list(tokens1.intersection(tokens2))
            
            # Calculate difference metrics
            total_unique_tokens = len(tokens1.union(tokens2))
            difference_ratio = len(only_in_text1) + len(only_in_text2)
            difference_percentage = (difference_ratio / total_unique_tokens * 100) if total_unique_tokens > 0 else 0
            
            return {
                'only_in_text1': only_in_text1[:20],  # Top 20 unique to text1
                'only_in_text2': only_in_text2[:20],  # Top 20 unique to text2
                'common_tokens': common_tokens[:20],   # Top 20 common tokens
                'difference_percentage': float(difference_percentage),
                'similarity_percentage': 100 - float(difference_percentage),
                'total_unique_tokens': total_unique_tokens,
                'text1_unique_count': len(only_in_text1),
                'text2_unique_count': len(only_in_text2),
                'common_count': len(common_tokens)
            }
            
        except Exception as e:
            logging.error(f"Error finding key differences: {str(e)}")
            return {'error': str(e)}