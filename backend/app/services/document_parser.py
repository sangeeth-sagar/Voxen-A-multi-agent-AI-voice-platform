import re
from typing import List
import urllib.request
from bs4 import BeautifulSoup
import pdfplumber

def split_text_recursive(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Splits text recursively based on paragraph breaks, sentence breaks, and space boundaries.
    """
    if not text:
        return []

    # Clean text whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # If we didn't reach the end of the text, try to find a natural boundary to split on
        if end < text_len:
            # Look backwards from 'end' up to 80 chars for punctuation or space
            split_points = [". ", "? ", "! ", " ", ", "]
            found = False
            for p in split_points:
                pos = text.rfind(p, start + chunk_size - 80, end)
                if pos != -1:
                    end = pos + len(p)
                    found = True
                    break
            # Fallback if no natural punctuation boundaries found
            if not found:
                pos = text.rfind(" ", start + chunk_size - 30, end)
                if pos != -1:
                    end = pos + 1
                    
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Calculate start point for next chunk considering overlap
        start = max(start + 1, end - chunk_overlap)
        
    return chunks


async def parse_pdf_bytes(file_bytes: bytes) -> str:
    """Extracts text from PDF bytes using pdfplumber."""
    import io
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text


async def parse_url(url: str) -> str:
    """Scrapes clean text from a web URL using BeautifulSoup."""
    import httpx
    async with httpx.AsyncClient(timeout=15.0) as client:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch URL. HTTP status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        text = soup.get_text()
        
        # Collapse multiple lines/whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)
