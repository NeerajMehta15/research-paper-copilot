# PDF parsing, chunking

import PyPDF2
import re
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
#from docx import Document as DocxDocument


def process_file(file_path):
    """Process file based on its type and extract content with metadata"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect file type and extract content
    if path.suffix.lower() == ".pdf":
        return _extract_pdf(file_path)
    elif path.suffix.lower() == ".docx":
        return _extract_docx(file_path)
    elif path.suffix.lower() in ['.txt', '.md']:
        return _extract_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def _extract_pdf(file_path):
    """Extracting details from the pdf file format including the metadata"""
    path = Path(file_path)
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                content += f"\n-------- Page {page_num+1} --------\n{page_text}"
                
        file_stats = path.stat()
        
        return {
            'content': content,
            'metadata': {
                'filename': path.name,
                'file_size': file_stats.st_size,
                'file_type': path.suffix.lower(),
                'character_count': len(content),
                'page_count': len(pdf_reader.pages)
            }
        }
    except Exception as e:
        raise Exception(f"Error processing PDF {file_path}: {str(e)}")


def _extract_docx(file_path):
    """Extract content from DOCX file"""
    path = Path(file_path)

    try:
        doc = DocxDocument(file_path)

        # Extract text from all paragraphs
        content = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])

        # Extract metadata
        file_stats = path.stat()

        return {
            'content': content,
            'metadata': {
                'filename': path.name,
                'file_size': file_stats.st_size,
                'file_type': path.suffix.lower(),
                'paragraph_count': len(doc.paragraphs),
                'character_count': len(content),
                'title': doc.core_properties.title or ''
            }
        }
    except Exception as e:
        raise Exception(f"Error processing DOCX {file_path}: {str(e)}")


def _extract_text(file_path: str) -> Dict[str, Any]:
    """Extract content from text files"""
    path = Path(file_path)
    
    try:
        # Access file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        file_stats = path.stat()
        
        return {
            'content': content,
            'metadata': {
                'filename': path.name,
                'file_size': file_stats.st_size,
                'file_type': path.suffix.lower(),
                'character_count': len(content)
            }
        }
    except Exception as e:
        raise Exception(f"Error processing text file {file_path}: {str(e)}")