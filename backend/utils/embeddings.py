import os
import logging
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding manager with sentence transformer model"""
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logging.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logging.error(f"Error loading embedding model: {str(e)}")
            self.model = None
            self.embedding_dimension = 384  # Default dimension
        
        # Initialize ChromaDB
        self.chroma_client = None
        self.collection = None
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            persist_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vector_store')
            os.makedirs(persist_directory, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=persist_directory)
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection(name="resume_job_embeddings")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="resume_job_embeddings",
                    metadata={"hnsw:space": "cosine"}
                )
            
            logging.info("ChromaDB vector store initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing vector store: {str(e)}")
            self.chroma_client = None
            self.collection = None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text"""
        if not self.model:
            return None
        
        try:
            # Clean and prepare text
            text = text.strip()
            if not text:
                return None
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Convert to percentage and ensure it's between 0 and 100
            similarity_percentage = max(0, min(100, (similarity + 1) * 50))
            
            return float(similarity_percentage)
            
        except Exception as e:
            logging.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def store_resume_embedding(self, resume_id: int, resume_text: str, 
                             metadata: Dict = None) -> bool:
        """Store resume embedding in vector database"""
        if not self.collection:
            return False
        
        try:
            embedding = self.generate_embedding(resume_text)
            if not embedding:
                return False
            
            # Prepare metadata
            meta = metadata or {}
            meta.update({
                'type': 'resume',
                'resume_id': resume_id,
                'text_length': len(resume_text)
            })
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[resume_text[:1000]],  # Store first 1000 chars as document
                metadatas=[meta],
                ids=[f"resume_{resume_id}"]
            )
            
            logging.info(f"Stored embedding for resume {resume_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing resume embedding: {str(e)}")
            return False
    
    def store_job_embedding(self, job_id: int, job_text: str, 
                          metadata: Dict = None) -> bool:
        """Store job description embedding in vector database"""
        if not self.collection:
            return False
        
        try:
            embedding = self.generate_embedding(job_text)
            if not embedding:
                return False
            
            # Prepare metadata
            meta = metadata or {}
            meta.update({
                'type': 'job',
                'job_id': job_id,
                'text_length': len(job_text)
            })
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[job_text[:1000]],  # Store first 1000 chars as document
                metadatas=[meta],
                ids=[f"job_{job_id}"]
            )
            
            logging.info(f"Stored embedding for job {job_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error storing job embedding: {str(e)}")
            return False
    
    def find_similar_resumes(self, job_text: str, limit: int = 10) -> List[Dict]:
        """Find resumes similar to job description"""
        if not self.collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(job_text)
            if not query_embedding:
                return []
            
            # Query similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"type": "resume"}
            )
            
            # Process results
            similar_resumes = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
                    metadata = results['metadatas'][0][i]
                    
                    similar_resumes.append({
                        'resume_id': metadata.get('resume_id'),
                        'similarity': similarity,
                        'similarity_percentage': similarity * 100,
                        'metadata': metadata
                    })
            
            return similar_resumes
            
        except Exception as e:
            logging.error(f"Error finding similar resumes: {str(e)}")
            return []
    
    def find_similar_jobs(self, resume_text: str, limit: int = 10) -> List[Dict]:
        """Find jobs similar to resume"""
        if not self.collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(resume_text)
            if not query_embedding:
                return []
            
            # Query similar documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"type": "job"}
            )
            
            # Process results
            similar_jobs = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
                    metadata = results['metadatas'][0][i]
                    
                    similar_jobs.append({
                        'job_id': metadata.get('job_id'),
                        'similarity': similarity,
                        'similarity_percentage': similarity * 100,
                        'metadata': metadata
                    })
            
            return similar_jobs
            
        except Exception as e:
            logging.error(f"Error finding similar jobs: {str(e)}")
            return []
    
    def get_semantic_similarity(self, resume_text: str, job_text: str) -> float:
        """Get semantic similarity between resume and job description"""
        try:
            resume_embedding = self.generate_embedding(resume_text)
            job_embedding = self.generate_embedding(job_text)
            
            if not resume_embedding or not job_embedding:
                return 0.0
            
            similarity = self.calculate_similarity(resume_embedding, job_embedding)
            return similarity
            
        except Exception as e:
            logging.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0
    
    def delete_resume_embedding(self, resume_id: int) -> bool:
        """Delete resume embedding from vector store"""
        if not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[f"resume_{resume_id}"])
            logging.info(f"Deleted embedding for resume {resume_id}")
            return True
        except Exception as e:
            logging.error(f"Error deleting resume embedding: {str(e)}")
            return False
    
    def delete_job_embedding(self, job_id: int) -> bool:
        """Delete job embedding from vector store"""
        if not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[f"job_{job_id}"])
            logging.info(f"Deleted embedding for job {job_id}")
            return True
        except Exception as e:
            logging.error(f"Error deleting job embedding: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector store collection"""
        if not self.collection:
            return {'error': 'Collection not available'}
        
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.peek(limit=min(100, count))
            
            resume_count = sum(1 for meta in sample_results.get('metadatas', []) 
                             if meta and meta.get('type') == 'resume')
            job_count = sum(1 for meta in sample_results.get('metadatas', []) 
                          if meta and meta.get('type') == 'job')
            
            return {
                'total_documents': count,
                'resume_documents': resume_count,
                'job_documents': job_count,
                'embedding_dimension': self.embedding_dimension
            }
            
        except Exception as e:
            logging.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}