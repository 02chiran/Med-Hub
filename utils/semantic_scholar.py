import requests

def search_semantic_scholar(query, max_results=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,abstract,year,authors"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    results = []
    for paper in data.get("data", []):
        authors = ", ".join([a.get("name","") for a in paper.get("authors",[])[:3]])
        results.append({"source": "SemanticScholar", "title": paper.get("title",""), "content": paper.get("abstract",""), "year": paper.get("year",""), "authors": authors})
    return results
