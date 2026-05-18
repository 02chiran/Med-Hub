from utils.pubmed_api import search_pubmed
from utils.europepmc_api import search_europepmc
from utils.semantic_scholar import search_semantic_scholar
from utils.wikipedia_api import search_wikipedia

def gather_clinical_evidence(query, use_pubmed=True, use_epmc=True, use_ss=True, use_wiki=True, max_results=5):
    evidence = []
    if use_pubmed:
        try: evidence.extend(search_pubmed(query, max_results=max_results))
        except Exception as e: evidence.append({"source": "PubMed", "title": "Error", "content": str(e)})
    if use_epmc:
        try: evidence.extend(search_europepmc(query, max_results=max_results))
        except Exception as e: evidence.append({"source": "EuropePMC", "title": "Error", "content": str(e)})
    if use_ss:
        try: evidence.extend(search_semantic_scholar(query, max_results=max_results))
        except Exception as e: evidence.append({"source": "SemanticScholar", "title": "Error", "content": str(e)})
    if use_wiki:
        try: evidence.extend(search_wikipedia(query))
        except Exception as e: evidence.append({"source": "Wikipedia", "title": "Error", "content": str(e)})
    return evidence
