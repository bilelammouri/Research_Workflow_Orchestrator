import pandas as pd
import json
import os

def rank_papers():
    # 1. Load data from Scopus Collector
    if not os.path.exists("scopus_metadata.csv"):
        print("[Error] scopus_metadata.csv not found.")
        return
    
    try:
        df_scopus = pd.read_csv("scopus_metadata.csv")
    except Exception as e:
        print(f"[Error] Failed to read metadata: {e}")
        return

    if df_scopus.empty:
        print("[Warn] Metadata is empty. Generating empty ranking.")
        with open("ranked_articles.json", "w") as f: json.dump([], f)
        return
    
    # Check for Column Existence (Defensive)
    # The collector now renames 'citedby-count' to 'citations'
    cit_col = 'citations' if 'citations' in df_scopus.columns else ('citedby-count' if 'citedby-count' in df_scopus.columns else None)
    
    if cit_col is None:
        print("[Warn] Citation column not found. Defaulting to 0.")
        df_scopus['citations_count'] = 0
    else:
        df_scopus['citations_count'] = pd.to_numeric(df_scopus[cit_col], errors='coerce').fillna(0)

    # 2. Load metric data from R Analysis Engine
    if os.path.exists("citation_metrics.csv"):
        try:
            df_r = pd.read_csv("citation_metrics.csv")
            df_scopus['clean_title'] = df_scopus.get('dc:title', '').astype(str).str.lower().str.strip()
            df_r['clean_title'] = df_r.get('TI', '').astype(str).str.lower().str.strip()
            
            df_merged = pd.merge(df_scopus, df_r[['clean_title', 'TC']], on='clean_title', how='left')
            df_merged['citations_count'] = df_merged['TC'].fillna(df_merged['citations_count'])
        except Exception as e:
            print(f"[Warn] R merge failed: {e}")
            df_merged = df_scopus
    else:
        df_merged = df_scopus

    # 3. Simple Ranking Logic
    df_merged['year_val'] = pd.to_numeric(df_merged.get('prism:coverDate', '2024').astype(str).str[:4], errors='coerce').fillna(2000)
    df_merged['rank_score'] = (df_merged['citations_count'] * 2) + (df_merged['year_val'] - 2000)
    
    df_final = df_merged.sort_values(by='rank_score', ascending=False)
    
    # 15 articles max
    top_n = df_final.head(15)
    
    result = []
    for _, row in top_n.iterrows():
        result.append({
            "title": row.get("dc:title", "Untitled"),
            "authors": row.get("dc:creator", "Anonymous"),
            "year": int(row.get("year_val", 2024)),
            "abstract": row.get("dc:description", ""),
            "journal": row.get("prism:publicationName", "Unknown"),
            "citations": int(row.get("citations_count", 0)),
            "doi": row.get("prism:doi", "")
        })
    
    with open("ranked_articles.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    
    print(f"[Ranker] Success: {len(result)} articles prioritized.")

if __name__ == "__main__":
    rank_papers()
