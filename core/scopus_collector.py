import pandas as pd
import requests
import time
import json
import os
from google import genai
from google.genai import types

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CONFIG_FILE = "agent_config.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "scopus_api_key": "ade7466450720df2422d3b3275ddc2a6",
        "article_count": 50,
        "project_title": "Intergenerational Equity in Decarbonization"
    }

def generate_boolean_query(theme, fallback=False):
    """Fallback manual query generation if AI is not used."""
    keywords = theme.replace("?", "").replace(".", "").replace(",", "")
    return f'TITLE-ABS-KEY("{keywords}")'

# ─────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────
def fetch_scopus_data(query, api_key, limit=50):
    print(f"[Collector] Querying Scopus: {query[:100]}...")
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    
    params = {
        "query": query,
        "count": min(limit, 25),
        "field": "eid,dc:title,dc:creator,prism:publicationName,prism:coverDate,prism:doi,citedby-count,dc:description,authkeywords,affiliation-name"
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            entries = data.get("search-results", {}).get("entry", [])
            
            if entries and "error" in entries[0]:
                print(f"[Warn] Scopus API Level Error: {entries[0]['error']}")
                return []
                
            return entries
        else:
            print(f"[Error] Scopus HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[Error] Connection failed: {e}")
    
    return []

def process_entries(entries):
    if not entries:
        return pd.DataFrame()
    
    df = pd.DataFrame(entries)
    if 'citedby-count' in df.columns:
        df = df.rename(columns={'citedby-count': 'citations'})
    elif 'citations' not in df.columns:
        df['citations'] = 0
        
    return df

def export_to_bibtex(df, filename="results.bib"):
    if df.empty:
        with open(filename, "w", encoding="utf-8") as f: f.write("")
        return

    lines = []
    for i, row in df.iterrows():
        ref_id = f"id{i+1}"
        title = str(row.get("dc:title", "No Title")).replace("{", "").replace("}", "")
        author = str(row.get("dc:creator", "Anonymous"))
        year = str(row.get("prism:coverDate", "2024"))[:4]
        doi = str(row.get("prism:doi", ""))
        journal = str(row.get("prism:publicationName", "Journal"))
        abstract = str(row.get("dc:description", ""))
        cit = str(row.get("citations", 0))
        keywords = str(row.get("authkeywords", "")).replace("|", "; ")
        affil = str(row.get("affiliation-name", ""))

        bib = f"@article{{{ref_id},\n"
        bib += f"  author = {{{author}}},\n"
        bib += f"  title = {{{title}}},\n"
        bib += f"  journal = {{{journal}}},\n"
        bib += f"  year = {{{year}}},\n"
        bib += f"  doi = {{{doi}}},\n"
        bib += f"  abstract = {{{abstract}}},\n"
        bib += f"  keywords = {{{keywords}}},\n"
        bib += f"  affiliation = {{{affil}}},\n"
        bib += f"  TC = {{{cit}}},\n"
        bib += f"  note = {{Citations: {cit}}}\n"
        bib += "}\n"
        lines.append(bib)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[Collector] BibTeX saved to {filename}")

if __name__ == "__main__":
    conf = get_config()
    theme = conf.get("theme_description", conf.get("project_title"))
    scopus_key = conf.get("scopus_api_key")
    gemini_key = conf.get("gemini_api_key")
    model_id = conf.get("model_name", "gemini-3.1-flash-lite-preview")
    limit = int(conf.get("article_count", 50))
    
    # 1. AI-Powered Query Generation
    q = None
    if gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
        try:
            client = genai.Client(api_key=gemini_key)
            q = suggest_boolean_query(client, model_id, theme)
        except Exception:
            q = generate_boolean_query(theme)
    else:
        q = generate_boolean_query(theme)
    
    # 2. Fetch Data
    data = fetch_scopus_data(q, scopus_key, limit)
    
    # 3. Fallback if empty AI query
    if not data:
        print("[Collector] No results for AI query. Attempting basic fallback...")
        q_fall = generate_boolean_query(theme)
        data = fetch_scopus_data(q_fall, scopus_key, limit)
        
    df = process_entries(data)
    if not df.empty:
        df.to_csv("scopus_metadata.csv", index=False)
        export_to_bibtex(df)
        print(f"[Collector] Success: {len(df)} articles archived.")
    else:
        pd.DataFrame(columns=['eid','dc:title','citations']).to_csv("scopus_metadata.csv", index=False)
        with open("results.bib", "w") as f: f.write("")
        print("[Collector] Final abort: No data found.")
