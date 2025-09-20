from typing import Dict, List, Optional
from transformers import pipeline
from backend.retrieval import retrieve_relevant_chunks
from openai import OpenAI
from backend.config import OPENAI_API_KEY

class RAGPipeline:
    def __init__(self, model_name="gpt-4o-mini", max_length=512, api_key=None):
        """Initialize RAG pipeline with OpenAI API"""
        self.model_name = model_name
        self.max_length = max_length
        
        # Use passed api_key or fall back to config
        if api_key is None:
            api_key = OPENAI_API_KEY
        
        if not api_key:
            raise ValueError("API key must be provided for LLM access")
    
        self.client = OpenAI(api_key=api_key)

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
        # Mode-specific prompt variations
        if mode == "normal":
            mode_instruction = (
                "Answer in exactly 2 lines: Line 1 should summarize the main finding/contribution. "
                "Line 2 should list sources using format: Sources: (Source 1), (Source 2). "
                "Base your answer ONLY on the provided context. If the context doesn't contain enough information to answer the question, "
                "write 'Insufficient information in provided sources to answer this question.' Use the exact citation format shown."
            )
        elif mode == "compare":
            mode_instruction = (
                "Compare in exactly 2 lines: Line 1 should state the key similarity or difference. "
                "Line 2 should cite which sources support each claim using format: Sources: (Source 1), (Source 2). "
                "Base comparison ONLY on the provided context. If the context doesn't contain enough information for comparison, "
                "write 'Insufficient information in provided sources for comparison.'"
            )
        elif mode == "simplify":
            mode_instruction = (
                "Explain in exactly 2 lines using simple language: Line 1 should give a plain English explanation. "
                "Line 2 should list sources using format: Sources: (Source 1), (Source 2). "
                "Avoid technical jargon. Base explanation ONLY on the provided context. If the context doesn't contain enough information, "
                "write 'Insufficient information in provided sources to explain this topic.'"
            )
                    
        return f"""
        {citation_instructions}
        
        CONTEXT: {formatted_context}
        QUESTION: {query}
        INSTRUCTION: {mode_instruction}
        
        ANSWER:
        """
    def _call_llm(self, prompt: str) -> str:
        """Make API call using OpenAI API"""
        print("=== DEBUG: Starting LLM call ===")
        print(f"Prompt length: {len(prompt)}")
        print(f"First 200 chars of prompt: {prompt[:200]}")

        try:
            print("Calling OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_length
            )

            answer = response.choices[0].message.content.strip()
            print(f"Generated answer: '{answer[:200]}'...")
            return answer

        except Exception as e:
            print(f"Error calling LLM: {e}")
            import traceback
            traceback.print_exc()
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
        rag = RAGPipeline(api_key=OPENAI_API_KEY)
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