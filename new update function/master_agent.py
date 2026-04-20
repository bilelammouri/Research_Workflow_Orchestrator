import subprocess
import os
import sys
import shutil

def find_r_executable():
    if shutil.which("Rscript"):
        return "Rscript"
    common_paths = [
        r"C:\Program Files\R\R-4.2.2\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.3.0\bin\Rscript.exe",
        r"C:\PROGRA~1\R\R-4.2.2\bin\Rscript.exe"
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None

def run_step(name, command):
    print(f"\n" + "="*50)
    print(f"  STEP: {name}")
    print("="*50)
    
    if command[0] == "Rscript":
        r_path = find_r_executable()
        if r_path:
            command[0] = r_path
        else:
            print("[ERROR] Rscript not found.")
            return False

    try:
        # All core scripts are now in the 'core/' directory
        result = subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"[ERROR] Step '{name}' failed.")
        return False
    except FileNotFoundError:
        print(f"[ERROR] Executable not found for: {name}")
        return False

def main():
    # 0. Check Gemini Key
    import json
    if os.path.exists("agent_config.json"):
        with open("agent_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            if config.get("gemini_api_key") == "YOUR_GEMINI_API_KEY_HERE":
                print("\n" + "!"*50)
                print("  [ACTION REQUIRED] PLEASE ADD YOUR GEMINI API KEY")
                print("  in 'agent_config.json' to enable synthesis.")
                print("!"*50 + "\n")
                sys.exit(1)

    # 1. Collection
    if not run_step("Scopus Data Collection", ["python", "core/scopus_collector.py"]):
        sys.exit(1)

    # 2. R Analysis
    if not run_step("Bibliometric R Analysis", ["Rscript", "core/analysis_engine.R"]):
        print("[Warn] R Analysis failed. Continuing with Scopus-only ranking...")

    # 3. Ranking
    if not run_step("Ranking & Filtering", ["python", "core/paper_ranker.py"]):
        sys.exit(1)

    # 4. Drafting & Compilation
    if not run_step("LaTeX Review Generation & PDF Build", ["python", "core/review_drafter.py"]):
        sys.exit(1)

    print("\n" + "="*50)
    print("  MISSION SUCCESSFUL")
    print("  Check 'core/' for data and the root for main.pdf")
    print("="*50)

if __name__ == "__main__":
    main()
