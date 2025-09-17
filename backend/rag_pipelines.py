from typing import Dict, List, Optional
from transformers import pipeline
from backend.retrieval import retrieve_relevant_chunks

class RAGPipeline:
    def __init__(self, model_name="microsoft/DialoGPT-medium", max_length=512):
        """Initialize RAG pipeline with Hugging Face pipeline"""
        self.model_name = model_name
        self.max_length = max_length
        
        # Initialize Hugging Face pipeline directly
        self.llm_pipeline = pipeline(
            "text-generation",
            model=model_name,
            tokenizer=model_name,
            max_length=max_length,
            do_sample=True,
            temperature=0.1
        )
    
    def generate_answer_with_citations(self, query: str, top_k: int = 5, mode: str = "normal"):
        """Main function to generate answers with citations"""
        context_data = retrieve_relevant_chunks(query, top_k)
        
        # Build prompt based on mode
        prompt = self._build_citation_prompt(context_data, mode)
        
        # Call LLM
        raw_response = self._call_llm(prompt)
        
        # Process and format response
        final_answer = self._process_llm_response(raw_response, context_data)
        
        return final_answer
        
    def _build_citation_prompt(self, context_data: Dict, mode: str) -> str:
        """Build prompt based on mode with citation instructions"""
        # Extract common components from the context data
        formatted_context = context_data['formatted_context']
        citation_map = context_data['citation_map'] 
        query = context_data['query']
        
        # Build citation instructions
        citation_instructions = "AVAILABLE SOURCES:\n"
        for source, reference in citation_map.items():
            citation_instructions += f"- {source}: {reference}\n"
        citation_instructions += "\nCite using format: (Source 1), (Source 2), etc."
        
        # Mode-specific prompt variations
        if mode == "normal":
            mode_instruction = "Answer the question using the context and cite sources."
        elif mode == "compare":
            mode_instruction = "Compare information across the sources and cite each claim."
        elif mode == "simplify":
            mode_instruction = "Explain in simple terms and cite sources."
            
        return f"""
        {citation_instructions}
        
        CONTEXT: {formatted_context}
        QUESTION: {query}
        INSTRUCTION: {mode_instruction}
        
        ANSWER:
        """
        
    def _call_llm(self, prompt: str) -> str:
        """Make API call using Hugging Face pipeline"""
        try:
            # Generate response using the pipeline
            response = self.llm_pipeline(prompt)
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            answer = generated_text[len(prompt):].strip()
            
            return answer
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "Error generating response"
    
    def _process_llm_response(self, raw_response: str, context_data: Dict) -> Dict:
        """Process and validate LLM response"""
        import re
        
        # Check if citations are present
        citation_pattern = r'\(Source \d+\)'
        citations_found = re.findall(citation_pattern, raw_response)
        has_citations = len(citations_found) > 0
        
        # Clean up the response
        cleaned_response = raw_response.strip()
        
        # Extract citation map for reference
        citation_map = context_data.get('citation_map', {})
        
        return {
            'answer': cleaned_response,
            'has_citations': has_citations,
            'citations_used': citations_found,
            'citation_map': citation_map,
            'query': context_data.get('query', ''),
            'sources_count': len(context_data.get('context_chunks', [])),
            'confidence': 'high' if has_citations else 'low'
        }

# Standalone function for simple usage
def answer_question_with_citations(query: str, mode: str = "normal") -> Dict:
    """Simple interface for generating cited answers"""
    try:
        rag = RAGPipeline()
        result = rag.generate_answer_with_citations(query, mode=mode)
        return result
    except Exception as e:
        return {
            'answer': f"Error generating answer: {str(e)}",
            'has_citations': False,
            'citations_used': [],
            'citation_map': {},
            'query': query,
            'sources_count': 0,
            'confidence': 'error'
        }