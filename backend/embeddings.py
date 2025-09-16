from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from backend.ingest import smart_chunking
import time 

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", db_path: str = "/Users/neeraj/Documents/Python/research-paper-copilot/data"):
        """Initialize embedding model and vector store"""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.vector_store = db_path
        self.client = chromadb.PersistentClient(path=self.vector_store)
        
        self.collection = self.client.get_or_create_collection(
            name="ai_research_paper",
            metadata={"description": "AI White paper documents"}
        )

    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(texts)
        return embeddings
    
    def store_chunks(self, chunks, doc_metadata, doc_id):
        """Store chunks with embeddings and metadata in vector database"""
        try:
            #extracting texts from chunks and generating embeddings    
            texts = [chunk['content'] for chunk in chunks]
            embeddings = self.generate_embeddings(texts)    
                
            #Prepare data from Chromadb
            documents = []
            chunk_metadata_list = []
            ids = []

            for i, chunk in enumerate(chunks):
                documents.append(chunk['content'])
                ids.append(f"{doc_id}_chunk_{i}")
                chunk_metadata_list.append({
                    'filename': doc_metadata['filename'], 
                    'doc_id': doc_id,
                    'page_number': chunk.get('page_number', None),
                    'title': doc_metadata.get('title', ''),
                    'chunk_id': i,
                    'length': chunk['length'],
                    'topic': 'ai research papers'
                })
                
            #Add details to the ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=chunk_metadata_list,
                ids=ids,
                embeddings=embeddings
            )
            return True
        except Exception as e:
            print(f"Error storing chunks: {e}")
            return False

    def add_document(self, processed_document):
        """Main function to add a processed document from ingest pipeline"""
        try:
            # Extract content and metadata from processed document
            chunks = processed_document['content']
            doc_metadata = processed_document['metadata']
            
            # Generate document ID
            doc_id = _generate_doc_id(doc_metadata['filename'])
            
            # Store chunks with embeddings
            success = self.store_chunks(chunks, doc_metadata, doc_id)
            
            if success:
                return doc_id
            else:
                return None
        except Exception as e:
            print(f"Error adding document: {e}")
            return None
    
    def search_similar(self, query: str, top_k: int = 5, filters: Optional[Dict] = None, min_similarity: float = 0.5):
        """Search for similar chunks"""
        try:
            # Generate query embedding
            query_embeddings = self.model.encode([query]).tolist() 
            
            # Search in vector store
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k
            )
            
            # Process and filter results
            filtered_results = []
            for doc, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                similarity = 1 - distance
                if similarity >= min_similarity: 
                    filtered_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity': similarity
                    })
            
            return sorted(filtered_results, key=lambda x: x['similarity'], reverse=True)
        except Exception as e:
            print(f"Error searching: {e}")
            return []
            
    def get_chunk_by_id(self, chunk_id):
        """Retrieve specific chunk by ID"""
        try:
            result = self.collection.get(ids=[chunk_id],
                                      include=['documents', 'metadatas', 'embeddings'])
            return result
        except Exception as e:
            print(f"Error retrieving chunk {chunk_id}: {e}")
            return None
    
    def delete_document(self, doc_id):
        """Delete all chunks belonging to a document"""
        try: 
            self.collection.delete(where={"doc_id": doc_id})
            print(f"Document {doc_id} and its chunks deleted.")
            return True
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")
            return False
    
    def list_documents(self, limit=100) -> List[Dict]:
        """List all stored documents with basic info"""
        try:
            collection_info = self.client.list_collections()
            return collection_info
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []

# Utility functions
def _generate_doc_id(filename):
    """Generate unique document ID"""
    from pathlib import Path
    file_stem = Path(filename).stem  # Just filename without extension
    unique_doc_id = f"doc_{file_stem}_{int(time.time())}"
    return unique_doc_id