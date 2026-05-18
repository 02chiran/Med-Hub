import requests

def search_europepmc(query, max_results=5):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": query, "format": "json", "pageSize": max_results, "resultType": "core"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    results = []
    for item in data.get("resultList", {}).get("result", []):
        results.append({"source": "EuropePMC", "title": item.get("title", ""), "pmid": item.get("id", ""), "content": item.get("abstractText", "")})
    return results
