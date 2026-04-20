from google import genai
import json
import os
import time

def diag():
    if not os.path.exists("agent_config.json"):
        print("Config missing")
        return
    with open("agent_config.json", "r") as f:
        config = json.load(f)
    
    api_key = config.get("gemini_api_key")
    models_to_test = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-3.1-flash-lite-preview"]
    
    client = genai.Client(api_key=api_key)
    
    for model_id in models_to_test:
        print(f"\n--- Testing model: {model_id} ---")
        try:
            response = client.models.generate_content(
                model=model_id,
                contents="Say hello"
            )
            print(f"Success! Response: {response.text}")
        except Exception as e:
            print(f"FAILED: {e}")
            if "RESOURCE_EXHAUSTED" in str(e):
                print("Confirmed: Quota issues.")
            time.sleep(2)

if __name__ == "__main__":
    diag()
