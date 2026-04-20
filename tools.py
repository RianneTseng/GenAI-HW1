import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import arxiv
import os

# --- 1. Real Weather Query (via wttr.in) ---
def get_weather(city: str):
    """Query real-time weather for a specific city."""
    try:
        # Use wttr.in for stable, developer-friendly weather data
        resp = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        if resp.status_code == 200:
            return f"Weather result: {resp.text}"
        return f"Unable to retrieve weather for {city} (Status: {resp.status_code})"
    except Exception as e:
        return f"Weather service error: {str(e)}"

# --- 2. Real Academic Search ---
def search_papers(query: str):
    """Search for real academic papers on arXiv."""
    search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
    results = []
    for result in search.results():
        results.append(f"Title: {result.title}\nLink: {result.pdf_url}")
    return "\n\n".join(results) if results else "No related papers found."

# --- 3. Real Web Scraping ---
def fetch_web_content(url: str):
    """Fetch content from a specific URL with User-Agent spoofing."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, timeout=5, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()
            
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text().strip() for p in paragraphs[:5]])
        return f"Page Title: {soup.title.string if soup.title else 'None'}\nSummary: {content[:400]}..."
    except Exception as e:
        return f"Scraping failed: {str(e)}"

# --- 4. CSV Data Analysis ---
def analyze_csv(file_path: str):
    """Read and analyze a local CSV file."""
    try:
        df = pd.read_csv(file_path)
        return f"Data Summary:\n{df.describe().to_string()}\nColumns: {list(df.columns)}"
    except Exception as e:
        return f"Analysis failed: {str(e)}"

# --- MCP Tool Definitions ---
tools_definition = [
    {"type": "function", "function": {"name": "get_weather", "description": "MUST be used for real-time weather. You MUST call this tool when asked about weather.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
    {"type": "function", "function": {"name": "search_papers", "description": "Search for academic papers on arXiv.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "fetch_web_content", "description": "Fetch web page content. Provide a full URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "analyze_csv", "description": "Analyze CSV file content.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}}
]

available_functions = {
    "get_weather": get_weather,
    "search_papers": search_papers,
    "fetch_web_content": fetch_web_content,
    "analyze_csv": analyze_csv
}