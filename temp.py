

# import os
# from dotenv import load_dotenv
# load_dotenv()
# import requests
# import json
# import re
# import time
# import random
# import inspect
# from pathlib import Path
# from typing import Optional

# # ---------- CONFIG ----------
# API_KEY = os.getenv("OPENROUTER_API_KEY")
# API_URL = "https://openrouter.ai/api/v1/chat/completions"
# MODEL = "openai/gpt-oss-20b:free"
# BASE_DIR = Path("user_files").resolve()
# BASE_DIR.mkdir(parents=True, exist_ok=True)

# # ----------------------------
# # ---------- Utilities / sandbox ----------
# def safe_resolve_under_base(path_str: str) -> Path:
#     p = (BASE_DIR / path_str).resolve()
#     if not str(p).startswith(str(BASE_DIR)):
#         raise ValueError("Access denied: path outside sandbox.")
#     return p

# def write_file(filename: str = None, path: str = None, content: str = "") -> dict:
#     """
#     Writes to disk. Accepts either 'filename' or 'path' (both map to the same).
#     """
#     target = path or filename
#     if not target:
#         return {"ok": False, "error": "no filename provided"}
#     try:
#         p = safe_resolve_under_base(target)
#         p.parent.mkdir(parents=True, exist_ok=True)
#         p.write_text(content or "", encoding="utf-8")
#         return {"ok": True, "filename": str(p.relative_to(BASE_DIR)), "message": f"Wrote to '{p.name}'"}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# def read_file(filename: str = None, path: str = None) -> dict:
#     target = path or filename
#     if not target:
#         return {"ok": False, "error": "no filename provided"}
#     try:
#         p = safe_resolve_under_base(target)
#         text = p.read_text(encoding="utf-8")
#         return {"ok": True, "filename": str(p.relative_to(BASE_DIR)), "content": text}
#     except FileNotFoundError:
#         return {"ok": False, "error": "file not found"}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# def list_files(path: str = "") -> dict:
#     try:
#         p = safe_resolve_under_base(path) if path else BASE_DIR
#         files = [str(f.relative_to(BASE_DIR)) for f in p.rglob("*") if f.is_file()]
#         return {"ok": True, "files": files}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# TOOL_REGISTRY = {
#     "createfile": write_file,
#     "write_file": write_file,
#     "read_file": read_file,
#     "list_files": list_files,
# }

# # Tools schema (advertised to models)
# TOOLS_SCHEMA = [
#     {
#         "type": "function",
#         "function": {
#             "name": "createfile",
#             "description": "Create or overwrite a text file in the sandbox. Args: filename, content, optional type.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "filename": {"type": "string"},
#                     "content": {"type": "string"},
#                     "type": {"type": "string"}
#                 },
#                 "required": ["filename", "content"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "read_file",
#             "description": "Read a text file. Args: filename",
#             "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "list_files",
#             "description": "List files under a path in the sandbox. Args: path (optional)",
#             "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
#         }
#     },
# ]

# # ---------- Helpers ----------
# def clean_code_fence(text: str) -> str:
#     text = text.strip()
#     if text.startswith("```") and text.endswith("```"):
#         parts = text.split("```")
#         if len(parts) >= 3:
#             return "```".join(parts[1:-1]).strip()
#         return text.strip("`")
#     return text

# def extract_first_json(text: str) -> Optional[dict]:
#     if not text:
#         return None
#     text = clean_code_fence(text)
#     start = text.find("{")
#     if start == -1:
#         return None
#     for end in range(start + 1, min(len(text), start + 8000)):
#         if text[end] == "}":
#             cand = text[start:end+1]
#             try:
#                 return json.loads(cand)
#             except Exception:
#                 continue
#     try:
#         return json.loads(text)
#     except Exception:
#         return None

# # Heuristic to find quoted content in user input
# QUOTE_RE = re.compile(r'["\'](.*?)["\']')

# def extract_user_provided_content(user_input: str) -> Optional[str]:
#     if not user_input:
#         return None
#     m = QUOTE_RE.search(user_input)
#     if m:
#         return m.group(1).strip()
#     patterns = [
#         r'and write (?:a |the )?(?:simple )?(.*?)$',
#         r'with content (.*?)$',
#         r'write (.*?)$',
#         r'contents?: (.*?)$',
#     ]
#     for pat in patterns:
#         mm = re.search(pat, user_input, re.IGNORECASE)
#         if mm:
#             return mm.group(1).strip(' ."\'')
#     return None

# # ---------- Local fallback simulator (unchanged, small) ----------
# def local_fallback_simulator(messages):
#     last_user = None
#     for m in reversed(messages):
#         if m.get("role") == "user":
#             last_user = m.get("content", "")
#             break
#     if not last_user:
#         content = json.dumps({"call":"assistant","message":"I am offline but ready to help."})
#         return {"choices":[{"message":{"content": content}}]}
#     lower = last_user.lower()
#     if ("create file" in lower) or ("create" in lower and "file" in lower):
#         user_content = extract_user_provided_content(last_user)
#         wants_generate = "generate" in lower or "generate a" in lower
#         mname = re.search(r'file\s+([A-Za-z0-9_\-\.]+)', last_user)
#         filename = mname.group(1) if mname else "untitled.txt"
#         if not user_content and wants_generate:
#             if filename.endswith(".js"):
#                 generated = "console.log('Hello, world!');"
#             elif filename.endswith(".py"):
#                 generated = "print('Hello, world!')"
#             else:
#                 generated = "Hello, world!"
#             args = {"filename": filename, "content": generated, "type": filename.split(".")[-1] if "." in filename else "text"}
#         else:
#             content_to_use = user_content or ""
#             args = {"filename": filename, "content": content_to_use, "type": filename.split(".")[-1] if "." in filename else "text"}
#         system_obj = {"call":"system","function":{"name":"createfile","args": args}}
#         return {"choices":[{"message":{"content": json.dumps(system_obj)}}]}
#     assistant_obj = {"call":"assistant","message":"(local fallback) I can't reach the API right now but here's a helpful reply."}
#     return {"choices":[{"message":{"content": json.dumps(assistant_obj)}}]}

# # ---------- Chat (retry + fallback) ----------
# def chat_with_ai(messages, temperature: float = 0.2, timeout: int = 60, max_retries: int = 5):
#     if not API_KEY:
#         print("⚠️ OPENROUTER_API_KEY not set. Using local fallback simulator.")
#         return local_fallback_simulator(messages)
#     headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
#     payload = {"model": MODEL, "messages": messages, "temperature": temperature, "tools": TOOLS_SCHEMA, "tool_choice": "auto"}
#     attempt = 0
#     while attempt <= max_retries:
#         attempt += 1
#         try:
#             r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
#             if 200 <= r.status_code < 300:
#                 try:
#                     return r.json()
#                 except Exception:
#                     print("❌ Failed to parse JSON; using fallback.")
#                     return local_fallback_simulator(messages)
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
#             print(f"❌ OpenRouter returned status {r.status_code}. Body: {r.text}")
#             return local_fallback_simulator(messages)
#         except requests.RequestException as e:
#             print(f"⚠️ Network error (attempt {attempt}/{max_retries}): {e}")
#             time.sleep(min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5))
#             continue
#     print("❌ Exhausted retries. Falling back to local simulator.")
#     return local_fallback_simulator(messages)

# # ---------- FIXED execute_tool_by_name ----------
# def execute_tool_by_name(name: str, args: dict, user_input_content: Optional[str]) -> dict:
#     """
#     Normalize args and call the function from TOOL_REGISTRY.
#     This carefully maps filename <-> path and passes only parameters the function accepts.
#     """
#     if not name:
#         return {"ok": False, "error": "no function name provided"}
#     func = TOOL_REGISTRY.get(name)
#     if not func:
#         return {"ok": False, "error": f"unknown function '{name}'"}
    
#     # normalize common keys
#     normalized = {}
#     if isinstance(args, dict):
#         for k, v in args.items():
#             lk = k.lower()
#             if lk in ("filename", "file", "path", "name"):
#                 normalized.setdefault("filename", v)
#                 normalized.setdefault("path", v)
#             elif lk in ("content", "body"):
#                 normalized["content"] = v
#             else:
#                 normalized[k] = v
#     elif isinstance(args, str):
#         normalized["content"] = args
    
#     # fallback to user-provided content if model did not provide content and user did
#     if "content" not in normalized and user_input_content:
#         normalized["content"] = user_input_content
    
#     # Inspect function signature and prepare kwargs that the function accepts
#     sig = inspect.signature(func)
#     func_kwargs = {}
#     for param in sig.parameters:
#         # supply filename/path/content if available
#         if param in normalized:
#             func_kwargs[param] = normalized[param]
    
#     # If function accepts 'path' but we only have 'filename', map it
#     if 'path' in sig.parameters and 'path' not in func_kwargs and 'filename' in normalized:
#         func_kwargs['path'] = normalized['filename']
#     if 'filename' in sig.parameters and 'filename' not in func_kwargs and 'path' in normalized:
#         func_kwargs['filename'] = normalized['path']
    
#     # Debug print: show exactly what we will call
#     print("→ Executing local function:", func.__name__, "with kwargs:", func_kwargs)
#     try:
#         return func(**func_kwargs)
#     except TypeError as e:
#         # last-resort: try calling with the normalized dict as keyword args
#         try:
#             print("⚠️ TypeError calling with restricted kwargs; trying full normalized dict as kwargs.")
#             return func(**normalized)
#         except Exception as ex:
#             return {"ok": False, "error": f"function call failed: {ex}"}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# # ---------- Main agent loop ----------
# SYSTEM_INSTRUCTION = (
#     "You MUST RESPOND with a single top-level JSON object only.\n"
#     "If you want the integration to execute a tool, reply with: "
#     '{"call":"system","function":{"name":"<tool_name>","args":{...}}}\n'
#     "If no tool is needed, reply with: {\"call\":\"assistant\",\"message\":\"...\"}\n"
#     "Supported tools: createfile (filename, content), read_file (filename), list_files (path).\n"
# )

# def main():
#     print("OpenRouter JSON-agent (fixed mapping). Type 'quit' or 'exit'.")
#     print("Files under:", BASE_DIR)
#     messages = [{"role":"system","content": SYSTEM_INSTRUCTION}]
    
#     while True:
#         try:
#             usr = input("\nYou: ").strip()
#         except (EOFError, KeyboardInterrupt):
#             print("\nBye.")
#             break
#         if not usr:
#             continue
#         if usr.lower() in ("quit", "exit"):
#             print("Bye.")
#             break
        
#         user_provided_content = extract_user_provided_content(usr)
#         messages.append({"role":"user","content": usr})
#         resp = chat_with_ai(messages)
        
#         if not resp:
#             print("No response.")
#             continue
        
#         tool_calls = resp.get("tool_calls") or []
#         assistant_raw = ""
#         choices = resp.get("choices", [])
#         if choices:
#             assistant_raw = choices[0].get("message", {}).get("content") or ""
#             if not tool_calls:
#                 tool_calls = choices[0].get("message", {}).get("tool_calls") or []
        
#         if tool_calls:
#             tc = tool_calls[0]
#             func_name = tc.get("function", {}).get("name") or tc.get("name") or tc.get("function_name")
#             params = tc.get("function", {}).get("arguments") or tc.get("function", {}).get("parameters") or tc.get("arguments") or tc.get("parameters") or {}
            
#             # FIX: Parse arguments if it's a JSON string
#             if isinstance(params, str):
#                 try:
#                     params = json.loads(params)
#                 except json.JSONDecodeError:
#                     print(f"⚠️ Failed to parse arguments as JSON: {params}")
#                     params = {}
            
#             if not func_name:
#                 print("Malformed tool_calls:", tc)
#                 messages.append({"role":"assistant","content":"Error: malformed tool_calls"})
#                 continue
            
#             print(f"Model requested tool: {func_name} with args: {params}")
#             result = execute_tool_by_name(func_name, params or {}, user_provided_content)
#             messages.append({"role":"function","name":func_name,"content": json.dumps(result)})
#             user_action = {"call":"user","action": {func_name: "success" if result.get("ok") else "error", "filename": result.get("filename",""), "detail": result.get("message") or result.get("error","")}}
#             messages.append({"role":"user","content": json.dumps(user_action)})
            
#             if result.get("ok"):
#                 print(f"✅ Tool succeeded: {result.get('filename')}  ({result.get('message')})")
#             else:
#                 print(f"❌ Tool failed: {result.get('error')}")
            
#             follow = chat_with_ai(messages)
#             if not follow:
#                 print("No follow-up.")
#                 continue
            
#             choices2 = follow.get("choices", [])
#             if choices2:
#                 final_content = choices2[0].get("message", {}).get("content") or ""
#                 parsed = extract_first_json(final_content)
#                 if parsed:
#                     print("\n🤖 AI (json):", json.dumps(parsed, indent=2))
#                 else:
#                     print("\n🤖 AI:", final_content.strip())
#                 messages.append({"role":"assistant","content": final_content})
#             continue
        
#         assistant_text = assistant_raw or (choices[0].get("message", {}).get("content") if choices else "")
#         parsed = extract_first_json(assistant_text)
        
#         if parsed and isinstance(parsed, dict) and parsed.get("call") == "system" and parsed.get("function"):
#             func = parsed["function"]
#             func_name = func.get("name")
#             args = func.get("args") or {}
            
#             # FIX: Parse args if it's a JSON string
#             if isinstance(args, str):
#                 try:
#                     args = json.loads(args)
#                 except json.JSONDecodeError:
#                     print(f"⚠️ Failed to parse args as JSON: {args}")
#                     args = {}
            
#             print(f"(fallback) Model requested function: {func_name} args={args}")
#             result = execute_tool_by_name(func_name, args, user_provided_content)
#             messages.append({"role":"function","name":func_name,"content": json.dumps(result)})
#             user_action = {"call":"user","action": {func_name: "success" if result.get("ok") else "error", "filename": result.get("filename",""), "detail": result.get("message") or result.get("error","")}}
#             messages.append({"role":"user","content": json.dumps(user_action)})
            
#             if result.get("ok"):
#                 print(f"✅ Tool succeeded: {result.get('filename')}  ({result.get('message')})")
#             else:
#                 print(f"❌ Tool failed: {result.get('error')}")
            
#             follow = chat_with_ai(messages)
#             if not follow:
#                 print("No follow-up.")
#                 continue
            
#             final = follow.get("choices", [])[0].get("message", {}).get("content", "")
#             parsed_final = extract_first_json(final)
#             if parsed_final:
#                 print("\n🤖 AI (json):", json.dumps(parsed_final, indent=2))
#             else:
#                 print("\n🤖 AI:", final.strip())
#             messages.append({"role":"assistant","content": final})
#             continue
        
#         if parsed and isinstance(parsed, dict) and parsed.get("call") == "assistant":
#             print("\n🤖 AI (assistant json):", json.dumps(parsed, indent=2))
#             messages.append({"role":"assistant","content": json.dumps(parsed)})
#         else:
#             raw = assistant_text or json.dumps(resp)
#             print("\n🤖 AI:", raw.strip())
#             messages.append({"role":"assistant","content": raw})

# if __name__ == "__main__":
#     main()


# test_gemini_keys.py

import os
import requests
import json
from dotenv import load_dotenv

def test_keys():
    """
    This script tests the Gemini API keys from your .env file.
    """
    print("--- Starting Gemini API Key Test ---")
    
    # 1. Load environment variables from .env file
    if load_dotenv():
        print("✅ .env file loaded successfully.")
    else:
        print("❌ WARNING: No .env file found in this directory.")
        return

    # 2. Read and parse the API keys
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    if not api_keys_str:
        print("❌ FAILURE: 'GEMINI_API_KEYS' not found in your .env file.")
        print("   Please ensure the variable is named correctly and has no typos.")
        return
        
    api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
    print(f"✅ Found {len(api_keys)} API key(s) to test.")

    # 3. Test each key against the Gemini API
    for i, key in enumerate(api_keys):
        print(f"\n--- Testing Key #{i+1} (ends with '...{key[-4:]}') ---")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "Hello"}]}]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Key #{i+1} is working correctly.")
                print(f"   API Response Snippet: {response.json()['candidates'][0]['content']['parts'][0]['text'][:30]}...")
            else:
                print(f"❌ FAILURE! Key #{i+1} is invalid or has issues.")
                print(f"   Status Code: {response.status_code}")
                print(f"   API Error Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ NETWORK ERROR on Key #{i+1}: Could not connect to the API.")
            print(f"   Details: {e}")
            
    print("\n--- Test Complete ---")


if __name__ == "__main__":
    test_keys()