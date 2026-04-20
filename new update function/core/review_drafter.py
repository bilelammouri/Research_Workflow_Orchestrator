import json
import os
import subprocess
import time
import random
from google import genai
from google.genai import types

def load_config():
    if not os.path.exists("agent_config.json"):
        return {}
    with open("agent_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_data():
    if os.path.exists("ranked_articles.json"):
        with open("ranked_articles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists("scopus_metadata.csv"):
        # Fallback to metadata if ranked json is missing
        import pandas as pd
        df = pd.read_csv("scopus_metadata.csv")
        return df.to_dict('records')
    return []

def latex_escape(text):
    """Simple escaping for LaTeX special characters."""
    chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
    }
    for k, v in chars.items():
        text = text.replace(k, v)
    return text

def initialize_client(config):
    api_key = config.get("gemini_api_key")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("[Error] Gemini API Key is missing in agent_config.json")
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"[Error] Failed to initialize Gemini Client: {e}")
        return None

def call_with_retry(client, model_id, prompt, config=None, max_retries=5):
    """Calls Gemini API with exponential backoff for rate limits."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config
            )
            return response.text.strip()
        except Exception as e:
            err_msg = str(e)
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                wait_time = (2 ** attempt) + random.random() + 5
                print(f"[Wait] Rate limit hit. Retrying in {wait_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"[Error] API Call failed: {err_msg}")
                return None
    return None

def generate_dynamic_structure(client, model_id, theme, articles):
    """Asks Gemini to propose a thematic outline for the literature review."""
    print("[Drafter] Planning dynamic structure...")
    
    article_list = ""
    for i, a in enumerate(articles[:15]): # Top 15 max
        title = a.get('dc:title', a.get('title', 'Unknown'))
        year = str(a.get('prism:coverDate', a.get('year', '2025')))[:4]
        article_list += f"[{i+1}] {title} ({year})\n"
    
    prompt = f"""
    You are a senior academic researcher. I am writing a Q1 journal literature review on the theme: "{theme}".
    Here is a list of the top relevant articles:
    {article_list}
    
    Task: Propose a logical, thematic structure for this review. 
    Return the result as a JSON array of strings (4-6 section titles).
    Return ONLY THE JSON ARRAY.
    """
    
    res = call_with_retry(client, model_id, prompt)
    if not res:
        return ["Theoretical Framework", "Methodological Innovations", "Global Policy Impacts", "Future Frontiers"]
        
    try:
        text = res.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        structure = json.loads(text)
        return structure
    except Exception as e:
        print(f"[Warn] Failed to parse structure: {e}. Using fallback.")
        return ["Theoretical Framework", "Methodological Innovations", "Global Policy Impacts", "Future Frontiers"]

def draft_section(client, model_id, theme, section_title, articles, target_words):
    """Drafts a specific section of the literature review."""
    print(f"[Drafter] Drafting section: {section_title}...")
    
    # Context Optimization: Limit abstracts to reduce token count
    context = ""
    for i, a in enumerate(articles[:15]):
        # Mapping differences between ranked JSON and raw CSV
        title = a.get('dc:title', a.get('title', 'Unknown'))
        author = a.get('dc:creator', a.get('authors', 'Anonymous'))
        year = str(a.get('prism:coverDate', a.get('year', '2025')))[:4]
        abstract = a.get('dc:description', a.get('abstract', 'No abstract available.'))
        context += f"ARTICLE {i+1}: Title: {title}\nAuthors: {author}\nYear: {year}\nAbstract: {abstract[:1200]}...\n\n"
    
    prompt = f"""
    You are writing a Q1 journal literature review in English.
    Theme: "{theme}"
    Section: "{section_title}" (~{target_words} words)
    
    Articles Data:
    {context}
    
    Instructions:
    1. Write a dense academic synthesis for this section with critical analysis.
    2. STRICT ADHERENCE: Focus exclusively on how the articles relate to the specific theme: "{theme}". If an article discusses other topics, emphasize only the parts relevant to this theme.
    3. Compare different perspectives found in the provided articles.
    4. You MUST use LaTeX citation format `\\citep{{idX}}` (X is the index 1 to {min(15, len(articles))}).
    5. Maintain a formal, doctoral-level tone. Use academic English.
    
    Return ONLY the LaTeX body text.
    """
    
    config = types.GenerateContentConfig(temperature=0.3)
    res = call_with_retry(client, model_id, prompt, config=config)
    return res if res else f"Error generating content for {section_title} after multiple retries."

def create_latex_master(config, content):
    title = config.get("project_title", "Research Report")
    author = config.get("author_name", "AI Agent")
    keywords = config.get("project_title", "").replace("?", "").replace(",", ";")
    
    master = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{natbib}
\usepackage{hyperref}
\usepackage{xcolor}
\geometry{margin=2.5cm}

\title{\textbf{""" + title + r"""}}
\author{""" + author + r"""}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
This report provides a systematic bibliometric analysis and synthetic literature review of high-impact research. It focuses specifically on the intersections of fiscal equity, wealth redistribution, and intergenerational justice.
\end{abstract}

\vspace{1em}
\noindent \textbf{Research Theme:} \textit{""" + title + r"""} \\
\textbf{Keywords:} \small """ + keywords + r"""

""" + content + r"""

\bibliographystyle{apalike}
\bibliography{results}

\end{document}
"""
    with open("main.tex", "w", encoding="utf-8") as f:
        f.write(master)

def run_compilation():
    print("[Drafter] Compiling PDF...")
    try:
        devnull = open(os.devnull, 'w')
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], check=False, stdout=devnull)
        subprocess.run(["bibtex", "main"], check=False, stdout=devnull)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], check=False, stdout=devnull)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], check=False, stdout=devnull)
        print("[Success] PDF complete: main.pdf")
    except Exception as e:
        print(f"[Warn] PDF build error: {e}")

if __name__ == "__main__":
    conf = load_config()
    articles = load_data()
    
    client = initialize_client(conf)
    if not client:
        exit(1)
        
    model_id = conf.get("model_name", "gemini-3.1-flash-lite-preview")
    theme = conf.get("project_title")
    
    # 1. Structure
    structure = generate_dynamic_structure(client, model_id, theme, articles)
    
    total_review_words = int(conf.get("review_word_count", 3000))
    intro_words = int(conf.get("intro_word_count", 300))
    words_per_section = total_review_words // len(structure)
    
    # 2. Intro
    print("[Drafter] Drafting Introduction...")
    intro_content = draft_section(client, model_id, theme, "Introduction", articles, intro_words)
    intro_content = latex_escape(intro_content)
    
    full_body = "\\section{Introduction}\n" + intro_content + "\n\n"
    
    # 3. Thematic Sections
    for section in structure:
        print(f"[Cooldown] Waiting 10s to stay under rate limits...")
        time.sleep(10)
        
        content = draft_section(client, model_id, theme, section, articles, words_per_section)
        content = latex_escape(content)
        full_body += f"\\section{{{section}}}\n" + content + "\n\n"
        
    create_latex_master(conf, full_body)
    run_compilation()
