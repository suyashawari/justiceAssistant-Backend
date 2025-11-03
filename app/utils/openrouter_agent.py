
# import os
# from dotenv import load_dotenv
# load_dotenv()
# import json
# import requests
# import time
# import random
# import re
# from datetime import datetime
# from app.utils.suspect_utils import extract_artifacts, inspect_urls, inspect_ips

# # ---------- CONFIG ----------
# API_KEY = os.getenv("OPENROUTER_API_KEY2")
# API_URL = "https://openrouter.ai/api/v1/chat/completions"
# MODEL = "openai/gpt-oss-20b:free"
# # MODEL = "google/gemini-flash-1.5"

# # ---------- TOOL REGISTRY ----------
# TOOL_REGISTRY = {
#     "extract_artifacts": extract_artifacts,
#     "inspect_urls": inspect_urls,
#     "inspect_ips": inspect_ips,
# }

# # ---------- TOOLS SCHEMA ----------
# TOOLS_SCHEMA = [
#     {
#         "type": "function",
#         "function": {
#             "name": "extract_artifacts",
#             "description": "Extracts digital artifacts (emails, URLs, IPs) from text. Only call this if you need to find emails, URLs, or IP addresses in the provided text.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "text": {"type": "string", "description": "The text to extract artifacts from"}
#                 },
#                 "required": ["text"]
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "inspect_urls",
#             "description": "Performs DNS and WHOIS lookups on URLs. Only call this if you have specific URLs that need investigation. Do not call if no URLs are available.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "urls": {"type": "array", "items": {"type": "string"}, "description": "List of URLs to investigate"}
#                 },
#                 "required": ["urls"]
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "inspect_ips",
#             "description": "Performs RDAP lookups on IP addresses. Only call this if you have specific IP addresses that need investigation. Do not call if no IPs are available.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "ips": {"type": "array", "items": {"type": "string"}, "description": "List of IP addresses to investigate"}
#                 },
#                 "required": ["ips"]
#             },
#         },
#     },
# ]

# # ---------- IMPROVED JSON PARSING ----------
# def clean_and_parse_json(text: str):
#     """
#     Aggressively clean and parse JSON that might be malformed.
#     """
#     if not text:
#         return {}
    
#     # Try direct parse first
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         pass
    
#     # Remove common issues
#     text = text.strip()
    
#     # Fix doubled quotes like ""url"" -> "url"
#     text = re.sub(r'""([^"]+)""', r'"\1"', text)
    
#     # Fix malformed arrays like [""]value"] -> ["value"]
#     text = re.sub(r'\[""\]([^"]+)"?\]', r'["\1"]', text)
    
#     # Fix concatenated values like [""]urlurl"] -> ["url"]
#     text = re.sub(r'\[""\]([^"]+)\1"?\]', r'["\1"]', text)
    
#     # Try to extract just the JSON object
#     json_match = re.search(r'\{.*\}', text, re.DOTALL)
#     if json_match:
#         try:
#             return json.loads(json_match.group(0))
#         except json.JSONDecodeError:
#             pass
    
#     # Try to fix specific patterns
#     # Pattern: {"urls": [""]value1value2"]}
#     array_match = re.search(r'\[""\]([^"\]]+)"?\]', text)
#     if array_match:
#         # Split on https:// or http:// if it's URLs
#         content = array_match.group(1)
#         if 'http' in content:
#             items = re.findall(r'https?://[^\s"]+', content)
#             if items:
#                 # --- CORRECTED BLOCK ---
#                 # Create a properly formatted string of JSON array items
#                 items_str = ','.join(f'"{item}"' for item in items)
#                 # Replace the malformed array with the corrected one
#                 text = re.sub(r'\[.*?\]', f'[{items_str}]', text)
#                 # --- END OF CORRECTION ---
    
#     # Last attempt
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError as e:
#         print(f"⚠️ JSON parse failed even after cleaning: {e}")
#         print(f"   Original: {text[:200]}")
#         return {}

# # ---------- CHAT FUNCTION WITH RETRY ----------
# def chat_with_openrouter(messages, temperature: float = 0.2, timeout: int = 90, max_retries: int = 5):
#     if not API_KEY:
#         print("❌ [AGENT ERROR] OpenRouter API key is missing.")
#         return None
    
#     headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
#     payload = {
#         "model": MODEL,
#         "messages": messages,
#         "temperature": temperature,
#         "tools": TOOLS_SCHEMA,
#         "tool_choice": "auto"
#     }
    
#     attempt = 0
#     while attempt <= max_retries:
#         attempt += 1
#         try:
#             print(f"[AGENT LOG] Sending context to OpenRouter AI (attempt {attempt})...")
#             r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            
#             if 200 <= r.status_code < 300:
#                 try:
#                     return r.json()
#                 except Exception:
#                     print("❌ Failed to parse JSON response.")
#                     return None
            
#             if r.status_code == 400:
#                 print(f"❌ Bad request (400). This might be a model issue.")
#                 print(f"   Response: {r.text[:500]}")
#                 # Don't retry 400s - it's likely a model/format issue
#                 return None
            
#             if r.status_code == 429:
#                 print(f"⚠️ Received 429 rate limit (attempt {attempt}/{max_retries}). Backing off...")
#                 sleep_for = min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5)
#                 time.sleep(sleep_for)
#                 continue
            
#             if 500 <= r.status_code < 600:
#                 print(f"⚠️ Server error {r.status_code} (attempt {attempt}/{max_retries}). Retrying...")
#                 sleep_for = min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5)
#                 time.sleep(sleep_for)
#                 continue
            
#             print(f"❌ OpenRouter returned status {r.status_code}. Body: {r.text[:500]}")
#             return None
            
#         except requests.RequestException as e:
#             print(f"⚠️ Network error (attempt {attempt}/{max_retries}): {e}")
#             time.sleep(min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5))
#             continue
    
#     print("❌ Exhausted retries.")
#     return None

# # ---------- EXECUTE TOOL ----------
# def execute_tool(function_name: str, function_args: dict):
#     """
#     Execute a tool from TOOL_REGISTRY with proper argument parsing.
#     Returns None if the tool shouldn't be called (missing required data).
#     """
#     if function_name not in TOOL_REGISTRY:
#         return {"error": f"Unknown function '{function_name}'"}
    
#     # Parse arguments if they're a JSON string
#     if isinstance(function_args, str):
#         try:
#             function_args = json.loads(function_args)
#         except json.JSONDecodeError:
#             print(f"⚠️ Failed to parse arguments, trying clean_and_parse_json...")
#             function_args = clean_and_parse_json(function_args)
#             if not function_args:
#                 return {"error": f"Could not parse arguments: {function_args}"}
    
#     # Validate required arguments - return None to skip if missing
#     if function_name == "inspect_ips":
#         ips = function_args.get("ips", [])
#         if not ips or not isinstance(ips, list) or len(ips) == 0:
#             print(f"⚠️ [AGENT] Skipping `{function_name}` - no IPs provided")
#             return None
#         # Filter out empty strings
#         ips = [ip for ip in ips if ip and str(ip).strip()]
#         if not ips:
#             print(f"⚠️ [AGENT] Skipping `{function_name}` - all IPs were empty")
#             return None
#         function_args["ips"] = ips
        
#     elif function_name == "inspect_urls":
#         urls = function_args.get("urls", [])
#         if not urls or not isinstance(urls, list) or len(urls) == 0:
#             print(f"⚠️ [AGENT] Skipping `{function_name}` - no URLs provided")
#             return None
#         # Filter out empty strings and clean URLs
#         urls = [url.strip() for url in urls if url and str(url).strip()]
#         # Additional cleaning: remove quotes and weird characters
#         urls = [re.sub(r'^["\']|["\']$', '', url) for url in urls]
#         urls = [url for url in urls if url.startswith('http')]
#         if not urls:
#             print(f"⚠️ [AGENT] Skipping `{function_name}` - all URLs were empty or invalid")
#             return None
#         function_args["urls"] = urls
#         print(f"   Cleaned URLs: {urls}")
        
#     elif function_name == "extract_artifacts":
#         text = function_args.get("text", "")
#         if not text or not str(text).strip():
#             print(f"⚠️ [AGENT] Skipping `{function_name}` - no text provided")
#             return None
    
#     print(f"[AGENT LOG] ✓ Executing tool: `{function_name}`")
    
#     try:
#         func = TOOL_REGISTRY[function_name]
#         result = func(**function_args)
#         return result
#     except Exception as e:
#         print(f"❌ [AGENT ERROR] Tool execution failed: {e}")
#         return {"error": str(e)}

# # ---------- MAIN ANALYSIS AGENT ----------
# def run_analysis_agent(text_to_analyze: str, report_id: int, file_path: str = None, max_turns: int = 8):
#     """
#     Run the forensic analysis agent with intelligent tool usage.
#     AI decides which tools to use based on available data.
#     """
#     findings = {
#         "tool_results": [],
#         "final_summary_text": "Analysis could not be completed.",
#         "conversation_history": [],
#         "errors": []
#     }
    
#     # Enhanced system prompt for intelligent tool usage
#     system_prompt = (
#         "You are a forensic investigation agent analyzing reports for digital artifacts and threats.\n\n"
#         "INSTRUCTIONS:\n"
#         "- Analyze the provided report text carefully.\n"
#         "- ONLY call tools when you have the required data and it's necessary for the investigation.\n"
#         "- If the report already contains clear information (IPs, URLs, emails), you can extract and analyze them directly.\n"
#         "- Do NOT call `inspect_urls` if there are no URLs to investigate.\n"
#         "- Do NOT call `inspect_ips` if there are no IP addresses to investigate.\n"
#         "- Use `extract_artifacts` only if you need to systematically find emails/URLs/IPs in large text.\n"
#         "- When calling tools, ensure your JSON is properly formatted.\n"
#         "- After your investigation, provide a clear summary of your findings.\n\n"
#         "Be efficient and accurate."
#     )
    
#     user_prompt = f"Analyze this forensic report (Report ID: {report_id}):\n\n{text_to_analyze}"
    
#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_prompt}
#     ]
    
#     print(f"\n{'='*60}")
#     print(f"Starting Forensic Analysis Agent for Report ID: {report_id}")
#     print(f"{'='*60}")
    
#     consecutive_errors = 0
#     max_consecutive_errors = 2
    
#     for turn in range(max_turns):
#         print(f"\n--- Agent Turn {turn + 1} ---")
        
#         response = chat_with_openrouter(messages)
#         if not response:
#             consecutive_errors += 1
#             error_msg = "Failed to get response from AI."
#             findings["errors"].append(f"Turn {turn + 1}: {error_msg}")
#             print(f"❌ [AGENT ERROR] {error_msg}")
            
#             if consecutive_errors >= max_consecutive_errors:
#                 print(f"❌ Too many consecutive errors ({consecutive_errors}). Ending analysis.")
#                 findings["final_summary_text"] = f"Analysis failed due to repeated errors. Last error: {error_msg}"
#                 return findings
#             continue
        
#         # Reset error counter on success
#         consecutive_errors = 0
        
#         # Extract the assistant message
#         choices = response.get("choices", [])
#         if not choices:
#             findings["errors"].append(f"Turn {turn + 1}: No choices in response")
#             print("❌ [AGENT ERROR] Empty response from AI.")
#             continue
        
#         message = choices[0].get("message", {})
        
#         # Check if the AI wants to call tools
#         tool_calls = message.get("tool_calls", [])
        
#         if tool_calls:
#             print(f"[AGENT LOG] AI requested {len(tool_calls)} tool call(s)")
            
#             # Track if any tools were actually executed
#             executed_any = False
            
#             # Execute each tool call
#             for tool_call in tool_calls:
#                 func_name = tool_call.get("function", {}).get("name")
#                 func_args_raw = tool_call.get("function", {}).get("arguments", {})
#                 tool_call_id = tool_call.get("id", f"call_{turn}_{random.randint(1000,9999)}")
                
#                 # Parse arguments - use improved parser
#                 if isinstance(func_args_raw, str):
#                     func_args = clean_and_parse_json(func_args_raw)
#                     if not func_args:
#                         print(f"⚠️ Could not parse arguments, skipping tool call")
#                         tool_message = {
#                             "role": "tool",
#                             "tool_call_id": tool_call_id,
#                             "name": func_name,
#                             "content": json.dumps({
#                                 "error": "Failed to parse arguments",
#                                 "skipped": True
#                             })
#                         }
#                         messages.append(tool_message)
#                         continue
#                 else:
#                     func_args = func_args_raw
                
#                 print(f"  → Tool requested: {func_name}")
                
#                 # Execute the tool (may return None if should be skipped)
#                 tool_output = execute_tool(func_name, func_args)
                
#                 if tool_output is None:
#                     # Tool was skipped - inform the AI
#                     tool_message = {
#                         "role": "tool",
#                         "tool_call_id": tool_call_id,
#                         "name": func_name,
#                         "content": json.dumps({
#                             "skipped": True,
#                             "reason": "Required data not provided or empty. No action taken."
#                         })
#                     }
#                     print(f"  ⊘ Skipped (insufficient data)")
#                 else:
#                     # Tool executed successfully
#                     executed_any = True
#                     findings["tool_results"].append({
#                         "turn": turn + 1,
#                         "tool": func_name,
#                         "args": func_args,
#                         "output": tool_output
#                     })
                    
#                     tool_message = {
#                         "role": "tool",
#                         "tool_call_id": tool_call_id,
#                         "name": func_name,
#                         "content": json.dumps(tool_output)
#                     }
#                     print(f"  ✅ Executed successfully")
                
#                 messages.append(tool_message)
#                 findings["conversation_history"].append(tool_message)
            
#             # Add the assistant message AFTER processing tools
#             messages.append(message)
#             findings["conversation_history"].append(message)
            
#             if not executed_any:
#                 print("  ℹ️  No tools were actually executed (all skipped due to missing data)")
        
#         else:
#             # No more tool calls - AI has provided final answer
#             print("[AGENT LOG] AI provided final analysis")
#             messages.append(message)
#             findings["conversation_history"].append(message)
            
#             content = message.get("content", "")
            
#             if content:
#                 # Try to parse as JSON, otherwise use as-is
#                 try:
#                     content_json = json.loads(content)
#                     findings["final_summary_text"] = content_json.get("summary", str(content_json))
#                 except (json.JSONDecodeError, TypeError):
#                     findings["final_summary_text"] = content
                
#                 print(f"\n{'='*60}")
#                 print("FINAL ANALYSIS SUMMARY:")
#                 print(f"{'='*60}")
#                 print(findings["final_summary_text"][:500])
#                 if len(findings["final_summary_text"]) > 500:
#                     print("... (truncated)")
#                 print(f"{'='*60}\n")
#             else:
#                 findings["final_summary_text"] = "Analysis completed with no additional commentary."
            
#             return findings
    
#     # If we exhausted all turns without a final answer
#     findings["final_summary_text"] = f"Investigation completed {len(findings['tool_results'])} tool operations but reached turn limit."
#     print(f"⚠️ [AGENT] Reached maximum turns ({max_turns})")
    
#     return findings
