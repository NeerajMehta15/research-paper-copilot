from backend.embeddings import EmbeddingManager

def retrieve_relevant_chunks(query, top_k=5):
    # Create EmbeddingManager instance
    embedding_manager = EmbeddingManager()

    #Checking if embeddings are available
    try:
        all_docs = embedding_manager.collection.get()
        print(f"Total documents in collection: {len(all_docs['documents'])}")
    except:
        print("Error accessing collection")
    
    # Get search results (this returns a list of dictionaries)
    search_results = embedding_manager.search_similar(query, top_k)
    
    # Format context and extract citations
    formatted_context = format_context_with_citations(search_results)
    citation_map = extract_citation_info(search_results)
    
    return {
        'query': query,
        'context_chunks': search_results,
        'formatted_context': formatted_context,
        'citation_map': citation_map
    }
    
    
#To transform the output so it is accessible to LLM        
def format_context_with_citations(search_results):
    formatted_context = []
    for i, result in enumerate(search_results, start=1):
        page_number = result.get('metadata', {}).get('page_number')
        content = result.get('content')
        formatted_context.append(f"Source {i} (Page {page_number}): {content}")
    return "\n".join(formatted_context)

#To extract citation info from metadata
def extract_citation_info(search_results):
    citation_map = {}
    for i, result in enumerate(search_results, start=1):
        metadata = result.get('metadata', {})
        filename = metadata.get('filename', 'Unknown')
        page_number = metadata.get('page_number', 'Unknown')
        citation_map[f"Source {i}"] = f"{filename}, Page {page_number}"
    return citation_map