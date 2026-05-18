import streamlit as st
import requests
from dotenv import load_dotenv
from utils.aggregator import gather_clinical_evidence
from utils.pdf_loader import search_pdf

load_dotenv()

st.set_page_config(page_title="Med Research Hub", page_icon="🩺", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.4rem; font-weight: 700; color: #1a6b4a; }
    .sub-header { font-size: 1rem; color: #555; margin-bottom: 1.5rem; }
    .source-badge { display:inline-block; background:#e6f4ee; color:#1a6b4a; border-radius:12px; padding:2px 10px; font-size:0.8rem; margin:2px; }
    .answer-box { background:#f8fdfb; border-left:4px solid #1a6b4a; padding:1rem 1.5rem; border-radius:6px; margin-top:1rem; }
    .stButton>button { background-color:#1a6b4a; color:white; border-radius:8px; padding:0.5rem 2rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

MEDICAL_KEYWORDS = [
    "disease", "symptom", "treatment", "drug", "medicine", "medical", "health",
    "doctor", "patient", "diagnosis", "therapy", "cancer", "diabetes", "virus",
    "bacteria", "infection", "surgery", "hospital", "clinical", "dose", "vaccine",
    "antibiotic", "blood", "heart", "brain", "lung", "kidney", "liver", "pain",
    "fever", "chronic", "acute", "disorder", "syndrome", "deficiency", "anatomy",
    "pharmacology", "physiology", "gene", "protein", "cell", "immune", "allergy",
    "pregnancy", "mental", "depression", "anxiety", "obesity", "hypertension",
    "stroke", "asthma", "arthritis", "alzheimer", "parkinson", "covid", "flu",
    "metformin", "insulin", "ibuprofen", "aspirin", "antiretroviral", "steroid"
]

def is_medical_query(query):
    query_lower = query.lower()
    return any(kw in query_lower for kw in MEDICAL_KEYWORDS)

def call_groq(prompt):
    """Call Groq API with llama3 - completely free"""
    import os
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return summarize_evidence_simple(prompt)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except:
        return summarize_evidence_simple(prompt)

def summarize_evidence_simple(prompt):
    """Fallback: summarize evidence without any LLM"""
    lines = []
    in_evidence = False
    sources_seen = []
    content_blocks = []

    for line in prompt.split("\n"):
        if line.startswith("SOURCE:"):
            src = line.replace("SOURCE:", "").strip()
            if src not in sources_seen:
                sources_seen.append(src)
            in_evidence = True
        elif line.startswith("CONTENT:") and in_evidence:
            content = line.replace("CONTENT:", "").strip()
            if content and len(content) > 50:
                content_blocks.append(content[:600])

    if not content_blocks:
        return "No sufficient evidence was found for this query. Please try a more specific medical term."

    result = "**Summary based on retrieved evidence:**\n\n"
    for i, block in enumerate(content_blocks[:4], 1):
        src = sources_seen[i-1] if i-1 < len(sources_seen) else "Source"
        result += f"**[{src}]** {block}...\n\n"
    result += "\n*Note: This is a direct extract from scientific databases. For a deeper AI-synthesised answer, add a GROQ_API_KEY to your .env file (free at groq.com).*"
    return result

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("## 🩺 Med Research Hub")
    st.markdown("*Evidence-based clinical query engine*")
    st.divider()
    st.markdown("### 📄 Upload a Clinical PDF")
    uploaded_pdf = st.file_uploader("Add a research paper", type=["pdf"])
    if uploaded_pdf:
        st.success(f"✅ Loaded: **{uploaded_pdf.name}**")
    st.divider()
    st.markdown("### ⚙️ Settings")
    max_sources = st.slider("Max results per source", 2, 8, 5)
    show_evidence = st.toggle("Show raw evidence panel", value=True)
    confidence_mode = st.selectbox("Response style", ["Clinical (concise)", "Detailed (verbose)", "Educational (simplified)"])
    st.divider()
    st.markdown("**Active Data Sources**")
    c1, c2 = st.columns(2)
    with c1:
        use_pubmed = st.checkbox("PubMed", value=True)
        use_epmc = st.checkbox("Europe PMC", value=True)
    with c2:
        use_ss = st.checkbox("Semantic Scholar", value=True)
        use_wiki = st.checkbox("Wikipedia", value=True)
    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

# ---- HEADER ----
st.markdown('<div class="main-header">🩺 Med Research Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered clinical research assistant — synthesising evidence from PubMed, Europe PMC, Semantic Scholar & Wikipedia</div>', unsafe_allow_html=True)

# ---- SEARCH ----
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input("Query", placeholder="e.g. What are the first-line treatments for Type 2 Diabetes?", label_visibility="collapsed")
with col_btn:
    submitted = st.button("🔍 Analyse", use_container_width=True)

st.markdown("**Try an example:**")
ex_cols = st.columns(4)
examples = ["Side effects of metformin", "What is myocardial infarction?", "mRNA vaccine mechanism", "Symptoms of Parkinson's disease"]
for i, ex in enumerate(examples):
    with ex_cols[i]:
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            query = ex
            submitted = True

# ---- MAIN LOGIC ----
if submitted and query:
    query = query.strip()

    if not is_medical_query(query):
        st.error("🚫 Med Research Hub only handles medical and health-related queries. Please rephrase.")
        st.stop()

    style_map = {
        "Clinical (concise)": "Be concise and use clinical terminology.",
        "Detailed (verbose)": "Be thorough with detailed explanations.",
        "Educational (simplified)": "Explain simply for a patient or student."
    }
    style_instruction = style_map.get(confidence_mode, "")

    with st.spinner("🔬 Searching clinical databases..."):
        try:
            evidence = gather_clinical_evidence(
                query,
                use_pubmed=use_pubmed,
                use_epmc=use_epmc,
                use_ss=use_ss,
                use_wiki=use_wiki,
                max_results=max_sources
            )

            if uploaded_pdf:
                pdf_bytes = uploaded_pdf.read()
                evidence = search_pdf(pdf_bytes, query) + evidence

            if not evidence:
                st.error("❌ No evidence found. Try a different query.")
                st.stop()

            combined_context = ""
            for item in evidence:
                combined_context += f"\nSOURCE: {item.get('source')}\nTITLE: {item.get('title','N/A')}\nCONTENT: {item.get('content','')}\n---\n"

            prompt = f"""You are Med Research Hub, a clinical evidence assistant.
STYLE: {style_instruction}
RULES:
- Only use the evidence below
- Never make up information
- Cite sources inline e.g. (PubMed)
- If evidence is insufficient, say so clearly

QUERY: {query}

EVIDENCE:
{combined_context}

SYNTHESISED CLINICAL ANSWER:"""

            answer = call_groq(prompt)

            st.markdown("---")
            st.markdown("### 📋 Clinical Summary")
            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

            sources_used = list({item.get("source") for item in evidence if item.get("source")})
            st.markdown("**Sources consulted:**")
            st.markdown(" ".join([f'<span class="source-badge">{s}</span>' for s in sources_used]), unsafe_allow_html=True)

            if show_evidence:
                with st.expander("📚 Raw Evidence Retrieved", expanded=False):
                    for idx, item in enumerate(evidence, 1):
                        st.markdown(f"**[{idx}] {item.get('source')} — {item.get('title','Untitled')}**")
                        content = item.get("content", "")
                        st.text(content[:600] + "..." if len(content) > 600 else content)
                        st.divider()

            st.session_state.history.insert(0, {"query": query, "answer": answer, "sources": sources_used})

        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

# ---- HISTORY ----
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 🕓 Recent Queries")
    for i, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"Q: {item['query']}", expanded=(i == 0)):
            st.markdown(item["answer"])
            st.caption(f"Sources: {', '.join(item['sources'])}")
