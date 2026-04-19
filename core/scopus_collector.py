import pandas as pd
import requests
import time
import json
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CONFIG_FILE = "agent_config.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "scopus_api_key": "",
        "article_count": 50,
        "project_title": "Intergenerational Equity in Decarbonization"
    }

def generate_boolean_query(theme, fallback=False):
    if fallback:
        # Simple keywords if advanced fails
        keywords = theme.replace("?", "").replace(".", "").replace(",", "")
        return f'TITLE-ABS-KEY("{keywords}")'
    
    # Advanced synonym expansion for robust search
    query = (
        'TITLE-ABS-KEY('
        '("decarbonization" OR "carbon pricing" OR "carbon tax" OR "climate policy") '
        'AND ("equity" OR "justice" OR "fairness") '
        'AND ("fiscal" OR "inequality" OR "wealth")'
        ')'
    )
    return query

# ─────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────
def fetch_scopus_data(query, api_key, limit=50):
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    
    params = {
        "query": query,
        "count": min(limit, 25),
        "field": "eid,dc:title,dc:creator,prism:publicationName,prism:coverDate,prism:doi,citedby-count,dc:description"
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            entries = data.get("search-results", {}).get("entry", [])
            
            # Check for API level error
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
    
    # RENAME citedby-count to citations (Fixing the Python KeyError)
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

        bib = f"@article{{{ref_id},\n"
        bib += f"  author = {{{author}}},\n"
        bib += f"  title = {{{title}}},\n"
        bib += f"  journal = {{{journal}}},\n"
        bib += f"  year = {{{year}}},\n"
        bib += f"  doi = {{{doi}}},\n"
        bib += f"  abstract = {{{abstract}}},\n"
        bib += f"  note = {{Citations: {cit}}}\n"
        bib += "}\n"
        lines.append(bib)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[Collector] BibTeX saved to {filename}")

if __name__ == "__main__":
    conf = get_config()
    theme = conf.get("project_title")
    api_key = conf.get("scopus_api_key")
    limit = int(conf.get("article_count", 50))
    
    # Attempt 1: Advanced Query
    q = generate_boolean_query(theme)
    data = fetch_scopus_data(q, api_key, limit)
    
    # Attempt 2: Fallback if empty
    if not data:
        print("[Collector] No results for advanced query. Attempting fallback keyword search...")
        q_fall = generate_boolean_query(theme, fallback=True)
        data = fetch_scopus_data(q_fall, api_key, limit)
        
    df = process_entries(data)
    if not df.empty:
        df.to_csv("scopus_metadata.csv", index=False)
        export_to_bibtex(df)
        print(f"[Collector] Success: {len(df)} articles archived.")
    else:
        # Create empty placeholder files to prevent script crashes down the line
        pd.DataFrame(columns=['eid','dc:title','citations']).to_csv("scopus_metadata.csv", index=False)
        with open("results.bib", "w") as f: f.write("")
        print("[Collector] Final abort: No data found even after fallback.")
