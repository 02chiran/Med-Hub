import wikipedia

def search_wikipedia(query, sentences=6):
    try:
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        page = wikipedia.page(query, auto_suggest=True)
        return [{"source": "Wikipedia", "title": page.title, "content": summary}]
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=sentences)
            return [{"source": "Wikipedia", "title": e.options[0], "content": summary}]
        except: return []
    except: return []
