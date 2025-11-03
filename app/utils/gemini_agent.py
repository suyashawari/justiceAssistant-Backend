

# import os
# from dotenv import load_dotenv
# load_dotenv()
# import json
# import requests
# import time
# import random
# import re
# import traceback
# import base64
# from app.utils.suspect_utils import TOOL_REGISTRY

# GEMINI_API_KEYS = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
# if not GEMINI_API_KEYS and os.getenv("GOOGLE_API_KEY"):
#     GEMINI_API_KEYS = [os.getenv("GOOGLE_API_KEY")]
# API_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
# MODEL = "gemini-flash-latest"

# MAX_TURNS = 10
# MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024

# def clean_and_parse_json(text: str):
#     if not text: return {}
#     text = text.strip()
#     if text.startswith("```json"):
#         text = text.lstrip("```json").rstrip("```")
#     elif text.startswith("```"):
#         text = text.lstrip("```").rstrip("```")
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
#         if json_match:
#             try:
#                 return json.loads(json_match.group(0))
#             except:
#                 pass
#     return {"purpose": "error", "error_message": "AI returned malformed JSON."}

# def get_file_mime_type(file_path):
#     ext = os.path.splitext(file_path)[1].lower()
#     if ext in ['.jpg', '.jpeg']:
#         return 'image/jpeg'
#     if ext == '.png':
#         return 'image/png'
#     if ext == '.pdf':
#         return 'application/pdf'
#     return None

# def chat_with_gemini(messages, current_key_index, temperature: float = 0.2, timeout: int = 180, max_retries: int = 3):
#     if not GEMINI_API_KEYS:
#         print("❌ [AGENT ERROR] No Gemini API keys configured.")
#         return {"purpose": "error", "error_message": "AI service is not configured."}, current_key_index
    
#     local_key_index = current_key_index
#     for attempt in range(max_retries):
#         current_key = GEMINI_API_KEYS[local_key_index % len(GEMINI_API_KEYS)]
#         url = f"{API_URL_BASE}?key={current_key}"
        
#         system_instruction = None
#         content_for_api = []
#         for m in messages:
#             if m['role'] == 'system':
#                 system_instruction = m['content']
#             else:
#                 role = 'model' if m['role'] in ['assistant', 'model'] else 'user'
#                 if 'parts' in m:
#                     content_for_api.append({'role': role, 'parts': m['parts']})
#                 else:
#                     content_for_api.append({'role': role, 'parts': [{'text': m['content']}]})
        
#         payload = {
#             "contents": content_for_api,
#             "system_instruction": {'parts': [{'text': system_instruction}]},
#             "generation_config": {
#                 "temperature": temperature,
#             }
#         }
        
#         try:
#             r = requests.post(url, json=payload, timeout=timeout)
#             if 200 <= r.status_code < 300:
#                 response_data = r.json()
#                 ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
#                 return clean_and_parse_json(ai_response_text), local_key_index
#             if r.status_code in [401, 403, 429]:
#                 print(f"🚫 Key failed with status {r.status_code}. Rotating key.")
#                 local_key_index += 1
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
            
#     return {"purpose": "error", "error_message": "All API keys failed or retries exhausted."}, local_key_index

# def run_analysis_agent(text_to_analyze: str, report_id: int, file_path: str = None):
#     current_key_index = 0
#     findings = {
#         "tool_results": [],
#         "final_summary_text": "Investigation Inconclusive: Agent failed to return a final summary.",
#         "errors": []
#     }
    
#     SYSTEM_PROMPT = (
#         "You are an autonomous Cyber Investigator. Your goal is to provide a comprehensive, evidence-backed summary of a cybercrime incident. "
#         "You will receive the user's report form data, pre-extracted file metadata, and potentially the evidence file itself. "
#         "Your responses MUST be a single, valid JSON object with the following structure:\n"
#         "1. **`purpose`**: [\"inspect_urls\", \"inspect_ips\", \"web_search\", \"summarize_findings\", \"stop_investigation\", \"error\"]\n"
#         "2. **`parameters`**: {args for the tool, e.g., {\"urls\": [...]}} (omit if summarizing/stopping)\n"
#         "3. **`final_summary`**: \"Your comprehensive final analysis text.\" (only include if purpose is \"summarize_findings\")\n\n"
#         "RULES:\n"
#         "- Your first step is to analyze all the provided information (form, metadata, file) and then decide which tool to use next.\n"
#         "- DO NOT call a tool named `extract_artifacts`. That has been done for you.\n"
#         "- Base your decisions ONLY on the evidence and tool results provided in the history.\n"
#         "- Do not call tools with empty data (e.g., inspect_urls with an empty list).\n"
#         f"- Maximum {MAX_TURNS} turns allowed. Use `summarize_findings` to stop the investigation."
#     )

#     initial_user_content = [
#         {'text': f"BEGIN ANALYSIS. Full Report Context:\n\n{text_to_analyze}"}
#     ]

#     if file_path and os.path.exists(file_path):
#         file_size = os.path.getsize(file_path)
#         if file_size < MAX_FILE_SIZE_BYTES:
#             print(f"File size ({file_size} bytes) is within limit. Uploading to AI.")
#             mime_type = get_file_mime_type(file_path)
#             if mime_type:
#                 try:
#                     with open(file_path, "rb") as f:
#                         file_data = base64.b64encode(f.read()).decode('utf-8')
                    
#                     initial_user_content.append({
#                         'inline_data': {
#                             'mime_type': mime_type,
#                             'data': file_data
#                         }
#                     })
#                 except Exception as e:
#                     print(f"Error encoding file for AI: {e}")
#             else:
#                 print(f"Unsupported file type for AI upload: {file_path}")
#         else:
#             print(f"File size ({file_size} bytes) exceeds limit. Not uploading file to AI.")

#     messages = [
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "parts": initial_user_content}
#     ]
    
#     print(f"\n{'='*60}\nStarting Gemini Multimodal Agent for Report ID: {report_id} (Max Turns: {MAX_TURNS})\n{'='*60}")
    
#     for turn in range(MAX_TURNS):
#         print(f"\n--- Agent Turn {turn + 1} / {MAX_TURNS} ---")
#         ai_response_json, new_key_index = chat_with_gemini(messages, current_key_index)
#         current_key_index = new_key_index
#         messages.append({"role": "model", "content": json.dumps(ai_response_json)})
        
#         purpose = ai_response_json.get("purpose", "error")
#         parameters = ai_response_json.get("parameters", {})
        
#         if purpose == "summarize_findings":
#             findings["final_summary_text"] = ai_response_json.get("final_summary", "Agent finished with a successful summary.")
#             print("[AGENT LOG] Final summary received. Investigation complete.")
#             return findings
            
#         if purpose == "stop_investigation":
#             findings["final_summary_text"] = "Agent explicitly stopped the investigation due to a dead end."
#             print("[AGENT LOG] Agent explicitly stopped. Investigation complete.")
#             return findings
            
#         if purpose == "error" or purpose not in TOOL_REGISTRY:
#             error_msg = ai_response_json.get("error_message", f"AI returned an unhandled error or unknown purpose: {purpose}")
#             findings["errors"].append(error_msg)
#             print(f"❌ [AGENT ERROR] {error_msg}")
#             findings["final_summary_text"] = f"Investigation Halted on Turn {turn + 1} due to error: {error_msg}. Finalizing report with partial findings."
#             return findings
            
#         if purpose in TOOL_REGISTRY:
#             tool_func = TOOL_REGISTRY[purpose]
#             print(f"[AGENT LOG] ✓ Executing tool: `{purpose}` with args: {list(parameters.keys())}")
#             tool_output = None
#             try:
#                 tool_output = tool_func(**parameters)
#                 findings["tool_results"].append({"tool": purpose, "args": parameters, "output": tool_output})
#                 messages.append({
#                     "role": "user",
#                     "content": f"TOOL_OUTPUT_FOR_{purpose}: {json.dumps(tool_output)}"
#                 })
#             except Exception as e:
#                 error_msg = f"Tool execution failed for {purpose}: {str(e)}"
#                 findings["errors"].append(error_msg)
#                 messages.append({
#                     "role": "user",
#                     "content": f"TOOL_EXECUTION_ERROR_FOR_{purpose}: {error_msg}"
#                 })
#                 print(f"❌ [TOOL ERROR] {error_msg}")
                
#     findings["final_summary_text"] = f"Investigation stopped: Maximum turns ({MAX_TURNS}) reached without a final summary. Finalizing report with partial findings."
#     print(f"⚠️ [AGENT] Reached maximum turns ({MAX_TURNS})")
#     findings['tool_results'] = findings.get('tool_results', [])
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
import base64
import logging
from datetime import datetime
from app.utils.suspect_utils import TOOL_REGISTRY

# --- AGENT LOGGER SETUP ---
# This sets up a logger to write to a file named 'agent_runs.log'
logger = logging.getLogger('AgentLogger')
if not logger.handlers:  # This check prevents adding handlers multiple times in development
    logger.setLevel(logging.INFO)
    # The log file will be created in the root directory where you run `python run.py`
    handler = logging.FileHandler('agent_runs.log')
    # Use a simple formatter to only output the message, as requested
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# --- END LOGGER SETUP ---


GEMINI_API_KEYS = [key.strip() for key in os.getenv("GEMINI_API_KEYS", "").split(",") if key.strip()]
if not GEMINI_API_KEYS and os.getenv("GOOGLE_API_KEY"):
    GEMINI_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

API_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
MODEL = "gemini-flash-latest"

MAX_TURNS = 10
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024

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

def get_file_mime_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    if ext == '.png':
        return 'image/png'
    if ext == '.pdf':
        return 'application/pdf'
    return None

def chat_with_gemini(messages, current_key_index, temperature: float = 0.2, timeout: int = 180, max_retries: int = 3):
    if not GEMINI_API_KEYS:
        error_msg = "❌ [AGENT ERROR] No Gemini API keys configured."
        logger.error(error_msg)
        print(error_msg)
        return {"purpose": "error", "error_message": "AI service is not configured."}, current_key_index
    
    local_key_index = current_key_index
    for attempt in range(max_retries):
        current_key = GEMINI_API_KEYS[local_key_index % len(GEMINI_API_KEYS)]
        url = f"{API_URL_BASE}?key={current_key}"
        
        system_instruction = None
        content_for_api = []
        for m in messages:
            if m['role'] == 'system':
                system_instruction = m['content']
            else:
                role = 'model' if m['role'] in ['assistant', 'model'] else 'user'
                if 'parts' in m:
                    content_for_api.append({'role': role, 'parts': m['parts']})
                else:
                    content_for_api.append({'role': role, 'parts': [{'text': m['content']}]})
        
        payload = {
            "contents": content_for_api,
            "system_instruction": {'parts': [{'text': system_instruction}]},
            "generation_config": {
                "temperature": temperature,
            }
        }
        
        try:
            # Log the request payload before sending
            log_payload = json.dumps(payload, indent=2)
            logger.info(f"REQUEST to Gemini:\n{log_payload}")
            
            r = requests.post(url, json=payload, timeout=timeout)

            if 200 <= r.status_code < 300:
                response_data = r.json()
                # Log the raw response from the AI
                log_response = json.dumps(response_data, indent=2)
                logger.info(f"RESPONSE from Gemini:\n{log_response}")

                ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                return clean_and_parse_json(ai_response_text), local_key_index
            
            error_details = f"Status: {r.status_code}, Response: {r.text}"
            logger.error(f"[API ERROR] {error_details}")

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
            error_message = f"Network error: {e}. Retrying..."
            logger.error(f"[AGENT ERROR] {error_message}")
            print(error_message)
            time.sleep(1.5 ** attempt)
        except Exception as e:
            error_message = f"General error: {e}. Failing."
            logger.error(f"[AGENT ERROR] {error_message}")
            print(error_message)
            return {"purpose": "error", "error_message": str(e)}, local_key_index
            
    final_error_msg = "All API keys failed or retries exhausted."
    logger.error(f"[AGENT ERROR] {final_error_msg}")
    return {"purpose": "error", "error_message": final_error_msg}, local_key_index

def run_analysis_agent(text_to_analyze: str, report_id: int, file_path: str = None):
    # Log the header for this specific report run
    logger.info("\n\n" + "="*20 + f" REPORT ID: {report_id} " + "="*20)
    logger.info(f"START TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    current_key_index = 0
    findings = {
        "tool_results": [],
        "final_summary_text": "Investigation Inconclusive: Agent failed to return a final summary.",
        "errors": []
    }
    
    SYSTEM_PROMPT = (
        "You are an autonomous Cyber Investigator. Your goal is to provide a comprehensive, evidence-backed summary of a cybercrime incident. "
        "You will receive the user's report form data, pre-extracted file metadata, and potentially the evidence file itself. "
        "Your responses MUST be a single, valid JSON object with the following structure:\n"
        "1. **`purpose`**: [\"inspect_urls\", \"inspect_ips\", \"web_search\", \"summarize_findings\", \"stop_investigation\", \"error\"]\n"
        "2. **`parameters`**: {args for the tool, e.g., {\"urls\": [...]}} (omit if summarizing/stopping)\n"
        "3. **`final_summary`**: \"Your comprehensive final analysis text.\" (only include if purpose is \"summarize_findings\")\n\n"
        "RULES:\n"
        "- Your first step is to analyze all the provided information (form, metadata, file) and then decide which tool to use next.\n"
        "- DO NOT call a tool named `extract_artifacts`. That has been done for you.\n"
        "- Base your decisions ONLY on the evidence and tool results provided in the history.\n"
        "- Do not call tools with empty data (e.g., inspect_urls with an empty list).\n"
        f"- Maximum {MAX_TURNS} turns allowed. Use `summarize_findings` to stop the investigation."
    )

    initial_user_content = [
        {'text': f"BEGIN ANALYSIS. Full Report Context:\n\n{text_to_analyze}"}
    ]

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size < MAX_FILE_SIZE_BYTES:
            print(f"File size ({file_size} bytes) is within limit. Uploading to AI.")
            mime_type = get_file_mime_type(file_path)
            if mime_type:
                try:
                    with open(file_path, "rb") as f:
                        file_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    initial_user_content.append({
                        'inline_data': {
                            'mime_type': mime_type,
                            'data': file_data
                        }
                    })
                except Exception as e:
                    print(f"Error encoding file for AI: {e}")
            else:
                print(f"Unsupported file type for AI upload: {file_path}")
        else:
            print(f"File size ({file_size} bytes) exceeds limit. Not uploading file to AI.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "parts": initial_user_content}
    ]
    
    start_message = f"Starting Gemini Multimodal Agent for Report ID: {report_id} (Max Turns: {MAX_TURNS})"
    logger.info("="*len(start_message))
    logger.info(start_message)
    logger.info("="*len(start_message))
    
    for turn in range(MAX_TURNS):
        logger.info(f"\n--- Agent Turn {turn + 1} / {MAX_TURNS} ---")
        print(f"\n--- Agent Turn {turn + 1} / {MAX_TURNS} ---")
        
        ai_response_json, new_key_index = chat_with_gemini(messages, current_key_index)
        current_key_index = new_key_index
        messages.append({"role": "model", "content": json.dumps(ai_response_json)})
        
        purpose = ai_response_json.get("purpose", "error")
        parameters = ai_response_json.get("parameters", {})
        
        logger.info(f"[AGENT LOG] AI decided on purpose: `{purpose}`")
        
        if purpose == "summarize_findings":
            findings["final_summary_text"] = ai_response_json.get("final_summary", "Agent finished with a successful summary.")
            log_msg = "[AGENT LOG] Final summary received. Investigation complete."
            logger.info(log_msg)
            print(log_msg)
            logger.info(f"END TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*55 + "\n")
            return findings
            
        if purpose == "stop_investigation":
            findings["final_summary_text"] = "Agent explicitly stopped the investigation due to a dead end."
            log_msg = "[AGENT LOG] Agent explicitly stopped. Investigation complete."
            logger.info(log_msg)
            print(log_msg)
            logger.info(f"END TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*55 + "\n")
            return findings
            
        if purpose == "error" or purpose not in TOOL_REGISTRY:
            error_msg = ai_response_json.get("error_message", f"AI returned an unhandled error or unknown purpose: {purpose}")
            findings["errors"].append(error_msg)
            log_msg = f"❌ [AGENT ERROR] {error_msg}"
            logger.error(log_msg)
            print(log_msg)
            findings["final_summary_text"] = f"Investigation Halted on Turn {turn + 1} due to error: {error_msg}. Finalizing report with partial findings."
            logger.info(f"END TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*55 + "\n")
            return findings
            
        if purpose in TOOL_REGISTRY:
            tool_func = TOOL_REGISTRY[purpose]
            log_msg = f"[AGENT LOG] ✓ Executing tool: `{purpose}` with args: {list(parameters.keys())}"
            logger.info(log_msg)
            print(log_msg)
            tool_output = None
            try:
                tool_output = tool_func(**parameters)
                findings["tool_results"].append({"tool": purpose, "args": parameters, "output": tool_output})
                # Log the output of the tool
                logger.info(f"[TOOL RESULT] Output for {purpose}:\n{json.dumps(tool_output, indent=2)}")
                messages.append({
                    "role": "user",
                    "content": f"TOOL_OUTPUT_FOR_{purpose}: {json.dumps(tool_output)}"
                })
            except Exception as e:
                error_msg = f"Tool execution failed for {purpose}: {str(e)}"
                findings["errors"].append(error_msg)
                log_msg = f"❌ [TOOL ERROR] {error_msg}"
                logger.error(log_msg)
                print(log_msg)
                messages.append({
                    "role": "user",
                    "content": f"TOOL_EXECUTION_ERROR_FOR_{purpose}: {error_msg}"
                })
                
    final_text = f"Investigation stopped: Maximum turns ({MAX_TURNS}) reached without a final summary. Finalizing report with partial findings."
    findings["final_summary_text"] = final_text
    log_msg = f"⚠️ [AGENT] Reached maximum turns ({MAX_TURNS})"
    logger.warning(log_msg)
    print(log_msg)
    findings['tool_results'] = findings.get('tool_results', [])
    
    logger.info(f"END TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*55 + "\n")
    return findings