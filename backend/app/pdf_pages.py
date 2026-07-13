"""
PDF page extraction and search functionality
Find which pages contain search terms
"""

from pathlib import Path
from typing import List, Dict, Optional
from PyPDF2 import PdfReader
import re


def find_pages_with_text(pdf_path: str, search_query: str) -> List[Dict]:
    """
    Find all pages in a PDF that contain text matching the search query

    Args:
        pdf_path: Path to PDF file
        search_query: Text to search for (can be multiple words)

    Returns:
        List of dicts with page numbers and text excerpts
        [{"page": 5, "excerpt": "...matching text...", "position": 0.3}, ...]
    """
    try:
        reader = PdfReader(pdf_path)
        query_terms = search_query.lower().split()

        matching_pages = []

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                page_text_lower = page_text.lower()

                # Check if any query term appears on this page
                matches = sum(1 for term in query_terms if term in page_text_lower)

                if matches > 0:
                    # Extract excerpt around first match
                    excerpt = extract_excerpt(page_text, query_terms[0], context=150)

                    # Calculate rough position in page (0.0 to 1.0)
                    first_match_pos = page_text_lower.find(query_terms[0])
                    position = first_match_pos / len(page_text) if len(page_text) > 0 else 0

                    matching_pages.append({
                        "page": page_num,
                        "excerpt": excerpt,
                        "matches": matches,
                        "position": position
                    })
            except Exception as e:
                # Skip pages that can't be read
                continue

        # Sort by number of matches (most relevant first)
        matching_pages.sort(key=lambda x: x['matches'], reverse=True)

        return matching_pages

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return []


def extract_excerpt(text: str, search_term: str, context: int = 150) -> str:
    """
    Extract text excerpt around the search term

    Args:
        text: Full page text
        search_term: Term to find
        context: Number of characters before/after (default 150)

    Returns:
        Text excerpt with ... prefix/suffix
    """
    text_lower = text.lower()
    search_term_lower = search_term.lower()

    pos = text_lower.find(search_term_lower)
    if pos == -1:
        # Term not found, return beginning of text
        return text[:context] + "..."

    # Extract context around the match
    start = max(0, pos - context)
    end = min(len(text), pos + len(search_term) + context)

    excerpt = text[start:end]

    # Add ellipsis if truncated
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."

    # Clean up whitespace
    excerpt = re.sub(r'\s+', ' ', excerpt).strip()

    return excerpt


def get_pdf_page_count(pdf_path: str) -> int:
    """Get total number of pages in PDF"""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except:
        return 0
