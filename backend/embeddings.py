# backend/embeddings.py
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
        self.collection = None
        self.client = chromadb.PersistentClient(path=self.vector_store)

    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(texts)
        return embeddings
    
    def store_chunks(self, chunks, doc_metadata):
        """Store chunks with embeddings and metadata in vector database"""
        #Generating a collection with the help of ChormaDB
        self.collection = self.client.get_or_create_collection(
            name = "ai_research_paper",
            metadata= {"description":"AI White paper documents"}
        )
        
        #Generating embeding from chunks
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
            
        #Prepare data from Chromadb
        documents = []
        chunk_metadata_list = []
        ids = []

        for i, chunk in enumerate(chunks):
            documents.append(chunk['content'])
            ids.append(f"chunk_{i}") 
            chunk_metadata_list.append({
                'filename': doc_metadata['filename'], 
                'chunk_id': i,
                'length': chunk['length'],
                'topic': 'ai research papers'
            })
            
        #Add details to the ChromaDB
        self.collection.add(
            documents=documents,
            metadatas= chunk_metadata_list,
            ids = ids,
            embeddings=embeddings
        )

    
    def add_document(self, processed_document):
        """Main function to add a processed document from ingest pipeline"""
    
        # Extract content and metadata from processed document
        content = processed_document['content']
        doc_metadata = processed_document['metadata']
        
        # Generate document ID
        doc_id = _generate_doc_id(doc_metadata['filename'])
        
        # Chunk the content using your smart_chunking function
        chunks = smart_chunking(content)
        
        # Add document metadata to each chunk
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            enhanced_chunk = {
                'content': chunk['content'],
                'length': chunk['length'],
                'doc_id': doc_id,
                'chunk_index': i
            }
            enhanced_chunks.append(enhanced_chunk)
        
        # Store chunks with embeddings
        self.store_chunks(enhanced_chunks, doc_metadata)
        
        # Return document ID for tracking
        return doc_id
    
    
    def search_similar(self, query: str, top_k: int = 5, filters: Optional[Dict] = None, min_similarity: float = 0.5) -> List[Dict]:
        """Search for similar chunks"""
        
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
            
        
    def get_chunk_by_id(self, chunk_id):
        """Retrieve specific chunk by ID"""
        try:
            temorary_ = self.collection.get(ids=[chunk_id],
                                        include=['documents', 'metadatas', 'embeddings'])
            return temorary_
        except Exception as e:
            print(f"Error retrieving chunk {chunk_id}: {e}")
    
    def delete_document(self, doc_id):
        """Delete all chunks belonging to a document"""
        try: 
            self.collection.delete(where={"doc_id": doc_id})
            print(f"Document {doc_id} and its chunks deleted.")
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")
        return
    
    def list_documents(self, limit = 100) -> List[Dict]:
        """List all stored documents with basic info"""
        try:
            collection_info = self.client.list_collections()
            return collection_info
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
        

# Utility functions
def _prepare_chunk_metadata(chunk, doc_metadata, chunk_index) -> Dict:
    """Prepare metadata for storing with embeddings"""
    pass
    

def _generate_chunk_id(doc_id, chunk_index):
    """Generate unique chunk ID"""
    try:
        return f"{doc_id}_chunk_{chunk_index}"
    except Exception as e:
        print(f"Error generating chunk ID: {e}")
        return None

def _generate_doc_id(file_path):
    """Generate unique document ID"""
    from pathlib import Path
    filename = Path(file_path).stem
    unique_doc_id = f"doc_{file_path}_{int(time.time())}"
    return unique_doc_id
    