import ssl, certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
from Bio import Entrez
Entrez.email = "medresearchhub@example.com"

def search_pubmed(query, max_results=5):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    ids = record["IdList"]
    if not ids: return []
    fetch_handle = Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml")
    records = Entrez.read(fetch_handle)
    results = []
    for article in records["PubmedArticle"]:
        try:
            data = article["MedlineCitation"]["Article"]
            title = str(data["ArticleTitle"])
            pmid = str(article["MedlineCitation"]["PMID"])
            abstract = " ".join([str(x) for x in data.get("Abstract", {}).get("AbstractText", [])])
            results.append({"source": "PubMed", "title": title, "pmid": pmid, "content": abstract})
        except: continue
    return results
