
# import os
# from dotenv import load_dotenv
# load_dotenv()
# import json
# import requests
# import time
# import random
# import re
# import traceback
# from app.utils.suspect_utils import TOOL_REGISTRY 

# # --- Configuration ---
# GEMINI_API_KEYS = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
# if not GEMINI_API_KEYS and os.getenv("GOOGLE_API_KEY"):
#     GEMINI_API_KEYS = [os.getenv("GOOGLE_API_KEY")] # Fallback to single key
# API_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
# MODEL = "gemini-flash-latest"
# MAX_TURNS = 10 # Explicitly set maximum turns for the state machine

# # --- Utility Functions ---

# def clean_and_parse_json(text: str):
#     if not text: return {}
    
#     # Try to clean code fences first
#     text = text.strip()
#     if text.startswith("```json"):
#         text = text.lstrip("```json").rstrip("```")
#     elif text.startswith("```"):
#         text = text.lstrip("```").rstrip("```")
        
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         # Fallback: attempt to find the first complete JSON object
#         json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
#         if json_match:
#             try:
#                 return json.loads(json_match.group(0))
#             except:
#                 pass
#     return {"purpose": "error", "error_message": "AI returned malformed JSON."}


# def chat_with_gemini(messages, current_key_index, temperature: float = 0.2, timeout: int = 90, max_retries: int = 3):
#     if not GEMINI_API_KEYS:
#         print("❌ [AGENT ERROR] No Gemini API keys configured.")
#         return {"purpose": "error", "error_message": "AI service is not configured."}, current_key_index
    
#     local_key_index = current_key_index
    
#     for attempt in range(max_retries):
#         current_key = GEMINI_API_KEYS[local_key_index % len(GEMINI_API_KEYS)]
#         url = f"{API_URL}?key={current_key}"
        
#         # Prepare the request payload
#         # For Gemini's new API structure, system instructions go in a special object
#         system_instruction = None
#         content_for_api = []
#         for m in messages:
#             if m['role'] == 'system':
#                 system_instruction = m['content']
#             else:
#                 # Gemini API expects 'model' role for AI responses, not 'assistant'
#                 role = 'model' if m['role'] in ['assistant', 'model'] else 'user'
#                 content_for_api.append({'role': role, 'parts': [{'text': m['content']}]})

#         payload = {
#             "contents": content_for_api,
#             "system_instruction": {'parts': [{'text': system_instruction}]},
#             "generation_config": {
#                 "temperature": temperature,
#             }
#         }
        
#         try:
#             r = requests.post(url, json=payload, timeout=timeout)
            
#             # Check for API errors (401, 429, 500)
#             if 200 <= r.status_code < 300:
#                 response_data = r.json()
#                 ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
#                 return clean_and_parse_json(ai_response_text), local_key_index
            
#             if r.status_code in [401, 403, 429]:
#                 print(f"🚫 Key failed with status {r.status_code}. Rotating key.")
#                 local_key_index += 1 # Rotate key on auth/rate limit failure
#                 time.sleep(1 + random.random())
#                 continue
                
#             if 500 <= r.status_code < 600:
#                 print(f"⚠️ Server error {r.status_code}. Retrying...")
#                 time.sleep(1.5 ** attempt)
#                 continue
                
#             print(f"❌ Unhandled status {r.status_code}. Failing. Response: {r.text}")
#             return {"purpose": "error", "error_message": f"API failed with status {r.status_code}"}, local_key_index

#         except requests.exceptions.RequestException as e:
#             print(f"Network error: {e}. Retrying...")
#             time.sleep(1.5 ** attempt)
            
#         except Exception as e:
#             print(f"General error: {e}. Failing.")
#             return {"purpose": "error", "error_message": str(e)}, local_key_index

#     # All retries/keys exhausted
#     return {"purpose": "error", "error_message": "All API keys failed or retries exhausted."}, local_key_index


# # --- NEW: Stateless Agent Workflow Engine ---

# def run_analysis_agent(text_to_analyze: str, report_id: int, file_path: str = None):
#     current_key_index = 0
    
#     findings = {
#         "tool_results": [],
#         "final_summary_text": "Investigation Inconclusive: Agent failed to return a final summary.",
#         "errors": []
#     }
    
#     # 1. Initial State: Define the autonomous system and initial prompt
#     SYSTEM_PROMPT = (
#         "You are an autonomous Cyber Investigator. Your goal is to provide a comprehensive, evidence-backed summary of the cybercrime incident."
#         "Your responses MUST be a single, valid JSON object with the following structure:\n"
#         "1. **`purpose`**: [\"extract_artifacts\", \"inspect_urls\", \"inspect_ips\", \"web_search\", \"summarize_findings\", \"stop_investigation\", \"error\"]\n"
#         "2. **`parameters`**: {args for the tool, e.g., {\"text\": \"...\"}} (omit if summarizing/stopping)\n"
#         "3. **`final_summary`**: \"Your comprehensive final analysis text.\" (only include if purpose is \"summarize_findings\")\n\n"
#         "RULES:\n"
#         "- Base your decisions ONLY on the evidence and tool results provided in the history.\n"
#         "- Do not call tools with empty data (e.g., inspect_urls with an empty list).\n"
#         f"- Maximum {MAX_TURNS} turns allowed. Use `summarize_findings` to stop the investigation."
#     )
    
#     # 2. Initial Messages: Start the conversation
#     messages = [
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": f"BEGIN ANALYSIS. Full Report Context:\n\n{text_to_analyze}"}
#     ]
    
#     print(f"\n{'='*60}\nStarting Gemini Stateless Agent for Report ID: {report_id} (Max Turns: {MAX_TURNS})\n{'='*60}")
    
#     # 3. Main State Machine Loop
#     for turn in range(MAX_TURNS):
#         print(f"\n--- Agent Turn {turn + 1} / {MAX_TURNS} ---")
        
#         # A. Get AI's next intended action (purpose)
#         ai_response_json, new_key_index = chat_with_gemini(messages, current_key_index)
#         current_key_index = new_key_index
        
#         # Log the AI's raw output/intent
#         messages.append({"role": "model", "content": json.dumps(ai_response_json)})
        
#         purpose = ai_response_json.get("purpose", "error")
#         parameters = ai_response_json.get("parameters", {})
        
#         # B. Handle Stopping Conditions
#         if purpose == "summarize_findings":
#             findings["final_summary_text"] = ai_response_json.get("final_summary", "Agent finished with a successful summary.")
#             print("[AGENT LOG] Final summary received. Investigation complete.")
#             return findings
            
#         if purpose == "stop_investigation":
#             findings["final_summary_text"] = "Agent explicitly stopped the investigation due to a dead end."
#             print("[AGENT LOG] Agent explicitly stopped. Investigation complete.")
#             return findings

#         # C. Handle Errors/Invalid Purpose
#         if purpose == "error" or purpose not in TOOL_REGISTRY:
#             error_msg = ai_response_json.get("error_message", f"AI returned an unhandled error or unknown purpose: {purpose}")
#             findings["errors"].append(error_msg)
#             print(f"❌ [AGENT ERROR] {error_msg}")
            
#             # If AI is stuck, force a final summary based on available data
#             findings["final_summary_text"] = f"Investigation Halted on Turn {turn + 1} due to error: {error_msg}. Finalizing report with partial findings."
#             return findings 
            
#         # D. Execute Tool
#         if purpose in TOOL_REGISTRY:
#             tool_func = TOOL_REGISTRY[purpose]
#             print(f"[AGENT LOG] ✓ Executing tool: `{purpose}` with args: {list(parameters.keys())}")
            
#             tool_output = None
#             try:
#                 tool_output = tool_func(**parameters)
#                 # *** THIS IS THE CORRECTED LINE ***
#                 findings["tool_results"].append({"tool": purpose, "args": parameters, "output": tool_output})
                
#                 # Send Tool Response Back to AI for next round of reasoning
#                 messages.append({
#                     "role": "user", 
#                     "content": f"TOOL_OUTPUT_FOR_{purpose}: {json.dumps(tool_output)}"
#                 })
                
#             except Exception as e:
#                 error_msg = f"Tool execution failed for {purpose}: {str(e)}"
#                 findings["errors"].append(error_msg)
                
#                 # Send Error Message Back to AI for next round of reasoning
#                 messages.append({
#                     "role": "user", 
#                     "content": f"TOOL_EXECUTION_ERROR_FOR_{purpose}: {error_msg}"
#                 })
#                 print(f"❌ [TOOL ERROR] {error_msg}")

#     # 4. Max Turns Reached
#     findings["final_summary_text"] = f"Investigation stopped: Maximum turns ({MAX_TURNS}) reached without a final summary. Finalizing report with partial findings."
#     print(f"⚠️ [AGENT] Reached maximum turns ({MAX_TURNS})")
#     return findings




import os
from dotenv import load_dotenv
load_dotenv()
import json
import requests
import time
import random
import re
import traceback
from app.utils.suspect_utils import TOOL_REGISTRY 

# --- Configuration ---
GEMINI_API_KEYS = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
if not GEMINI_API_KEYS and os.getenv("GOOGLE_API_KEY"):
    GEMINI_API_KEYS = [os.getenv("GOOGLE_API_KEY")] # Fallback to single key

API_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
MODEL = "gemini-flash-latest"

MAX_TURNS = 10 # Explicitly set maximum turns for the state machine

# --- Utility Functions ---

def clean_and_parse_json(text: str):
    if not text: return {}
    
    text = text.strip()
    if text.startswith("```json"):
        text = text.lstrip("```json").rstrip("```")
    elif text.startswith("```"):
        text = text.lstrip("```").rstrip("```")
        
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
    return {"purpose": "error", "error_message": "AI returned malformed JSON."}


def chat_with_gemini(messages, current_key_index, temperature: float = 0.2, timeout: int = 90, max_retries: int = 3):
    if not GEMINI_API_KEYS:
        print("❌ [AGENT ERROR] No Gemini API keys configured.")
        return {"purpose": "error", "error_message": "AI service is not configured."}, current_key_index
    
    local_key_index = current_key_index
    
    for attempt in range(max_retries):
        current_key = GEMINI_API_KEYS[local_key_index % len(GEMINI_API_KEYS)]
        
        # *** THIS IS THE CORRECTED LINE ***
        url = f"{API_URL_BASE}?key={current_key}"
        # **********************************

        system_instruction = None
        content_for_api = []
        for m in messages:
            if m['role'] == 'system':
                system_instruction = m['content']
            else:
                role = 'model' if m['role'] in ['assistant', 'model'] else 'user'
                content_for_api.append({'role': role, 'parts': [{'text': m['content']}]})

        payload = {
            "contents": content_for_api,
            "system_instruction": {'parts': [{'text': system_instruction}]},
            "generation_config": {
                "temperature": temperature,
            }
        }
        
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            
            if 200 <= r.status_code < 300:
                response_data = r.json()
                ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                return clean_and_parse_json(ai_response_text), local_key_index
            
            if r.status_code in [401, 403, 429]:
                print(f"🚫 Key failed with status {r.status_code}. Rotating key.")
                local_key_index += 1
                time.sleep(1 + random.random())
                continue
                
            if 500 <= r.status_code < 600:
                print(f"⚠️ Server error {r.status_code}. Retrying...")
                time.sleep(1.5 ** attempt)
                continue
                
            print(f"❌ Unhandled status {r.status_code}. Failing. Response: {r.text}")
            return {"purpose": "error", "error_message": f"API failed with status {r.status_code}"}, local_key_index

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}. Retrying...")
            time.sleep(1.5 ** attempt)
            
        except Exception as e:
            print(f"General error: {e}. Failing.")
            return {"purpose": "error", "error_message": str(e)}, local_key_index

    return {"purpose": "error", "error_message": "All API keys failed or retries exhausted."}, local_key_index


# --- NEW: Stateless Agent Workflow Engine ---

def run_analysis_agent(text_to_analyze: str, report_id: int, file_path: str = None):
    current_key_index = 0
    
    findings = {
        "tool_results": [],
        "final_summary_text": "Investigation Inconclusive: Agent failed to return a final summary.",
        "errors": []
    }
    
    SYSTEM_PROMPT = (
        "You are an autonomous Cyber Investigator. Your goal is to provide a comprehensive, evidence-backed summary of the cybercrime incident."
        "Your responses MUST be a single, valid JSON object with the following structure:\n"
        "1. **`purpose`**: [\"extract_artifacts\", \"inspect_urls\", \"inspect_ips\", \"web_search\", \"summarize_findings\", \"stop_investigation\", \"error\"]\n"
        "2. **`parameters`**: {args for the tool, e.g., {\"text\": \"...\"}} (omit if summarizing/stopping)\n"
        "3. **`final_summary`**: \"Your comprehensive final analysis text.\" (only include if purpose is \"summarize_findings\")\n\n"
        "RULES:\n"
        "- Base your decisions ONLY on the evidence and tool results provided in the history.\n"
        "- Do not call tools with empty data (e.g., inspect_urls with an empty list).\n"
        f"- Maximum {MAX_TURNS} turns allowed. Use `summarize_findings` to stop the investigation."
    )
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"BEGIN ANALYSIS. Full Report Context:\n\n{text_to_analyze}"}
    ]
    
    print(f"\n{'='*60}\nStarting Gemini Stateless Agent for Report ID: {report_id} (Max Turns: {MAX_TURNS})\n{'='*60}")
    
    for turn in range(MAX_TURNS):
        print(f"\n--- Agent Turn {turn + 1} / {MAX_TURNS} ---")
        
        ai_response_json, new_key_index = chat_with_gemini(messages, current_key_index)
        current_key_index = new_key_index
        
        messages.append({"role": "model", "content": json.dumps(ai_response_json)})
        
        purpose = ai_response_json.get("purpose", "error")
        parameters = ai_response_json.get("parameters", {})
        
        if purpose == "summarize_findings":
            findings["final_summary_text"] = ai_response_json.get("final_summary", "Agent finished with a successful summary.")
            print("[AGENT LOG] Final summary received. Investigation complete.")
            return findings
            
        if purpose == "stop_investigation":
            findings["final_summary_text"] = "Agent explicitly stopped the investigation due to a dead end."
            print("[AGENT LOG] Agent explicitly stopped. Investigation complete.")
            return findings

        if purpose == "error" or purpose not in TOOL_REGISTRY:
            error_msg = ai_response_json.get("error_message", f"AI returned an unhandled error or unknown purpose: {purpose}")
            findings["errors"].append(error_msg)
            print(f"❌ [AGENT ERROR] {error_msg}")
            findings["final_summary_text"] = f"Investigation Halted on Turn {turn + 1} due to error: {error_msg}. Finalizing report with partial findings."
            return findings 
            
        if purpose in TOOL_REGISTRY:
            tool_func = TOOL_REGISTRY[purpose]
            print(f"[AGENT LOG] ✓ Executing tool: `{purpose}` with args: {list(parameters.keys())}")
            
            tool_output = None
            try:
                tool_output = tool_func(**parameters)
                findings["tool_results"].append({"tool": purpose, "args": parameters, "output": tool_output})
                
                messages.append({
                    "role": "user", 
                    "content": f"TOOL_OUTPUT_FOR_{purpose}: {json.dumps(tool_output)}"
                })
                
            except Exception as e:
                error_msg = f"Tool execution failed for {purpose}: {str(e)}"
                findings["errors"].append(error_msg)
                
                messages.append({
                    "role": "user", 
                    "content": f"TOOL_EXECUTION_ERROR_FOR_{purpose}: {error_msg}"
                })
                print(f"❌ [TOOL ERROR] {error_msg}")

    findings["final_summary_text"] = f"Investigation stopped: Maximum turns ({MAX_TURNS}) reached without a final summary. Finalizing report with partial findings."
    print(f"⚠️ [AGENT] Reached maximum turns ({MAX_TURNS})")
    findings['tool_results'] = findings.get('tool_results', [])
    return findings