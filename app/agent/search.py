import os
from typing import TypedDict, List, Optional, cast
from tavily import TavilyClient

class SearchResult(TypedDict):
    url: str
    title: str
    content: str
    score: float
    raw_content: Optional[str]

class SearchResponse(TypedDict):
    query: str
    follow_up_questions: Optional[str]
    answer: Optional[str]
    images: List[str]
    results: List[SearchResult]
    response_time: float

def search(query: str) -> SearchResponse:
    
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(query, limit=5)
    return cast(SearchResponse, response)
