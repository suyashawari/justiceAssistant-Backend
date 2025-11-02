

# import os
# import os
# from dotenv import load_dotenv  # <-- ADD THIS LINE

# load_dotenv()  # <-- ADD THIS LINE to load variables from .env

# import requests
# import json
# import requests
# import json
# import re
# from pathlib import Path
# from datetime import datetime

# # ========== CONFIG ==========

# # API_KEY = "sk-or-v1-kjh"


# # --- Constants ---
# API_KEY = os.getenv("OPENROUTER_API_KEY")
# print(API_KEY)
# API_URL = "https://openrouter.ai/api/v1/chat/completions"
# MODEL ="openai/gpt-oss-20b:free"

# BASE_DIR = Path("user_files").resolve()  # sandbox directory for created files
# BASE_DIR.mkdir(parents=True, exist_ok=True)

# # ===========================


# # ---------- file utility functions ----------
# def read_file(filename: str = None, path: str = None) -> str:
#     """Read the text content of a file (supports 'filename' or 'path')."""
#     target = (path or filename)
#     if not target:
#         return "Error: no filename or path provided."
#     p = (BASE_DIR / target).resolve()
#     if not str(p).startswith(str(BASE_DIR)):
#         return "Error: access denied (outside base directory)."
#     try:
#         return p.read_text(encoding="utf-8")
#     except FileNotFoundError:
#         return f"Error: file '{target}' not found."
#     except Exception as e:
#         return f"Error reading file '{target}': {e}"


# def write_file(filename: str = None, path: str = None, content: str = "") -> str:
#     """Write text content to a file (supports 'filename' or 'path')."""
#     target = (path or filename)
#     if not target:
#         return "Error: no filename or path provided."
#     p = (BASE_DIR / target).resolve()
#     if not str(p).startswith(str(BASE_DIR)):
#         return "Error: access denied (outside base directory)."
#     try:
#         p.parent.mkdir(parents=True, exist_ok=True)
#         p.write_text(content or "", encoding="utf-8")
#         return f"✅ Wrote to '{target}' successfully."
#     except Exception as e:
#         return f"Error writing file '{target}': {e}"


# # registry of available functions
# FUNCTIONS = {
#     "read_file": read_file,
#     "write_file": write_file,
# }


# # ---------- helpers for cleaning / parsing ----------
# # Remove specific tool blocks and any <|...|> tokens; also remove stray 'assistantcommentary' text
# _TOOL_BLOCK_RE = re.compile(r"<\|start\|>assistant.*?<\|call\|>", re.DOTALL)
# _GENERIC_TOKEN_RE = re.compile(r"<\|[^>]*\|>")
# _META_COMMENTARY_RE = re.compile(r"(assistant)?commentary\s*to=.*?\{.*?\}", re.DOTALL)
# _JSON_INLINE_RE = re.compile(r"(\{.*\})", re.DOTALL)


# def clean_tool_markup(text: str) -> str:
#     """Strip tool-style tokens and leftover meta text; return cleaned natural text."""
#     if not text:
#         return ""
#     # remove explicit tool blocks like <|start|>assistant ... <|call|>
#     text = _TOOL_BLOCK_RE.sub("", text)
#     # remove "assistantcommentary to=..." or similar
#     text = _META_COMMENTARY_RE.sub("", text)
#     # remove any <|...|> tokens left
#     text = _GENERIC_TOKEN_RE.sub("", text)
#     # remove words like 'json' or 'commentary' appearing alone
#     text = re.sub(r"\b(json|commentary|assistant)\b", "", text)
#     # collapse whitespace
#     text = re.sub(r"\s+", " ", text).strip()
#     return text


# # robust parse of tool-style function call (OpenRouter style)
# TOOL_CALL_RE = re.compile(
#     r"to=functions\.([a-zA-Z_][a-zA-Z0-9_]*)"
#     r".*?<\|message\|>(\{.*?\})<\|call\|>",
#     re.DOTALL
# )


# def parse_function_call(text: str):
#     """
#     Return (name, args_dict) or None.
#     Will attempt to recover from slightly different forms.
#     """
#     if not text:
#         return None
#     m = TOOL_CALL_RE.search(text)
#     if m:
#         name = m.group(1)
#         js_text = m.group(2)
#         try:
#             args = json.loads(js_text)
#         except json.JSONDecodeError:
#             try:
#                 args = json.loads(js_text.replace("'", '"'))
#             except Exception:
#                 args = {}
#         return name, args

#     # loosened fallback: find 'to=functions.NAME' and then first JSON after it
#     m2 = re.search(r"to=functions\.([a-zA-Z_][a-zA-Z0-9_]*)", text)
#     if not m2:
#         return None
#     name = m2.group(1)
#     after = text[m2.end():]
#     jsm = _JSON_INLINE_RE.search(after)
#     if not jsm:
#         return name, {}
#     try:
#         args = json.loads(jsm.group(1))
#     except Exception:
#         args = {}
#     return name, args


# # ---------- OpenRouter chat helper ----------
# def chat_with_ai(messages, temperature: float = 0.2, timeout: int = 60, function_call: str | None = None):
#     """
#     Send messages to OpenRouter.
#     function_call: None (omit), "none" (request no function), or "auto"
#     """
#     payload = {
#         "model": MODEL,
#         "messages": messages,
#         "temperature": temperature,
#     }
#     if function_call is not None:
#         payload["function_call"] = function_call

#     headers = {
#         "Authorization": f"Bearer {API_KEY}",
#         "Content-Type": "application/json",
#     }
#     try:
#         r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
#         r.raise_for_status()
#     except requests.RequestException as e:
#         print("❌ Request failed:", e)
#         try:
#             print("Response body:", r.text)
#         except Exception:
#             pass
#         return None
#     try:
#         return r.json()
#     except Exception:
#         print("❌ Failed to parse JSON response.")
#         return None


# # ---------- main loop ----------
# def main():
#     print("OpenRouter function-calling demo (system prompt enforced).")
#     print("Files under:", BASE_DIR)
#     print("Type 'quit' or 'exit' to stop.\n")

#     # Strong system prompt telling the model to use functions for file management
#     system_msg = (
#         "You are a helpful assistant specialized in file management. "
#         "When the user asks to create, read, update, append, or delete files, "
#         "you MUST emit a tool-style function call (e.g. to=functions.write_file with JSON args) "
#         "so the integration runs the corresponding function. "
#         "Available functions: read_file(filename/path) and write_file(filename/path, content). "
#         "After receiving the function result, reply with a short natural-language acknowledgement (do NOT repeat the tool markup)."
#     )

#     messages = [
#         {"role": "system", "content": system_msg}
#     ]

#     while True:
#         user = input("\nYou: ").strip()
#         if not user:
#             continue
#         if user.lower() in ("quit", "exit"):
#             print("👋 Bye.")
#             break

#         # append user message and send to model
#         messages.append({"role": "user", "content": user})
#         resp = chat_with_ai(messages)
#         if not resp:
#             continue

#         choice = resp.get("choices", [{}])[0]
#         assistant_msg = choice.get("message") or {}
#         raw_content = assistant_msg.get("content") or ""
#         print("\n🤖 AI (raw):", raw_content.strip())

#         # Check for tool-style function call in the raw content
#         call = parse_function_call(raw_content)
#         if call:
#             fn_name, fn_args = call
#             print("🧩 Parsed function call:", fn_name, fn_args)

#             # Normalize argument keys to support filename/path etc.
#             normalized_args = {}
#             if isinstance(fn_args, dict):
#                 for k, v in fn_args.items():
#                     if k in ("filename", "file", "path", "name"):
#                         normalized_args.setdefault("filename", v)
#                         normalized_args.setdefault("path", v)
#                     else:
#                         normalized_args[k] = v
#             elif isinstance(fn_args, str):
#                 normalized_args["content"] = fn_args

#             # Execute function if available
#             if fn_name in FUNCTIONS:
#                 try:
#                     output = FUNCTIONS[fn_name](**normalized_args)
#                 except TypeError:
#                     try:
#                         output = FUNCTIONS[fn_name](**(fn_args if isinstance(fn_args, dict) else {}))
#                     except Exception as e:
#                         output = f"Error executing function: {e}"
#                 except Exception as e:
#                     output = f"Error executing function: {e}"

#                 print("🔧 Function result:", output)

#                 # Always append function-role message with the result so model can use it
#                 messages.append({
#                     "role": "function",
#                     "name": fn_name,
#                     "content": str(output)
#                 })

#                 # Request a normal assistant reply (no further function call)
#                 follow = chat_with_ai(messages, function_call="none")
#                 if not follow:
#                     # fallback: print our own ack
#                     cleaned_ack = str(output)
#                     print("\n🤖 AI (final, fallback):", cleaned_ack)
#                     messages.append({"role": "assistant", "content": cleaned_ack})
#                     continue

#                 choice2 = follow.get("choices", [{}])[0]
#                 assistant2 = choice2.get("message") or {}
#                 final_text = assistant2.get("content") or ""
#                 cleaned = clean_tool_markup(final_text)

#                 # If cleaned reply is empty or nonsense, fallback to sensible ack using function result
#                 if not cleaned:
#                     # If it was a write, return a clear path-based confirmation
#                     if fn_name == "write_file":
#                         fname = normalized_args.get("filename") or normalized_args.get("path") or ""
#                         full_path = (BASE_DIR / fname).resolve() if fname else None
#                         if full_path:
#                             cleaned = f"File '{fname}' created successfully at:\n  {full_path}"
#                         else:
#                             cleaned = str(output)
#                     else:
#                         cleaned = str(output)

#                 # Print cleaned final reply
#                 print("\n🤖 AI (final, cleaned):", cleaned.strip())

#                 # If write_file, also print explicit full path (helpful)
#                 if fn_name == "write_file":
#                     fname = normalized_args.get("filename") or normalized_args.get("path") or ""
#                     if fname:
#                         full_path = (BASE_DIR / fname).resolve()
#                         print(f"\n📁 Full path: {full_path}")

#                 # append assistant final reply for context
#                 messages.append({"role": "assistant", "content": cleaned})
#             else:
#                 print("❌ Unknown function requested by model:", fn_name)
#                 messages.append({"role": "assistant", "content": f"Error: unknown function '{fn_name}'."})
#         else:
#             # No function call: clean tokens and display
#             cleaned_reply = clean_tool_markup(raw_content)
#             if cleaned_reply:
#                 print("\n🤖 AI (reply, cleaned):", cleaned_reply)
#                 messages.append({"role": "assistant", "content": cleaned_reply})
#             else:
#                 # nothing meaningful after cleaning -> show raw and keep it
#                 print("\n🤖 AI (reply):", raw_content.strip())
#                 messages.append({"role": "assistant", "content": raw_content})


# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
"""
OpenRouter JSON-agent for file creation / reading / listing.
Behavior:
 - Ask the model to reply ONLY with JSON.
 - If model requests a tool call (system JSON), execute it locally.
 - Return a user-action JSON back to the model and get a final assistant response.
 - If model doesn't require a tool, it should return assistant JSON and we print it.
"""
#!/usr/bin/env python3
"""
OpenRouter JSON-agent (fixed execute_tool_by_name mapping bug).
- Normalizes args and inspects the Python function signature before calling,
  so 'filename'/'path' are passed correctly.
- Keeps retry/backoff and local fallback simulator from previous script.
"""

import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import re
import time
import random
import inspect
from pathlib import Path
from typing import Optional

# ---------- CONFIG ----------
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-20b:free"
BASE_DIR = Path("user_files").resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------
# ---------- Utilities / sandbox ----------
def safe_resolve_under_base(path_str: str) -> Path:
    p = (BASE_DIR / path_str).resolve()
    if not str(p).startswith(str(BASE_DIR)):
        raise ValueError("Access denied: path outside sandbox.")
    return p

def write_file(filename: str = None, path: str = None, content: str = "") -> dict:
    """
    Writes to disk. Accepts either 'filename' or 'path' (both map to the same).
    """
    target = path or filename
    if not target:
        return {"ok": False, "error": "no filename provided"}
    try:
        p = safe_resolve_under_base(target)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "", encoding="utf-8")
        return {"ok": True, "filename": str(p.relative_to(BASE_DIR)), "message": f"Wrote to '{p.name}'"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def read_file(filename: str = None, path: str = None) -> dict:
    target = path or filename
    if not target:
        return {"ok": False, "error": "no filename provided"}
    try:
        p = safe_resolve_under_base(target)
        text = p.read_text(encoding="utf-8")
        return {"ok": True, "filename": str(p.relative_to(BASE_DIR)), "content": text}
    except FileNotFoundError:
        return {"ok": False, "error": "file not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_files(path: str = "") -> dict:
    try:
        p = safe_resolve_under_base(path) if path else BASE_DIR
        files = [str(f.relative_to(BASE_DIR)) for f in p.rglob("*") if f.is_file()]
        return {"ok": True, "files": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}

TOOL_REGISTRY = {
    "createfile": write_file,
    "write_file": write_file,
    "read_file": read_file,
    "list_files": list_files,
}

# Tools schema (advertised to models)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "createfile",
            "description": "Create or overwrite a text file in the sandbox. Args: filename, content, optional type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file. Args: filename",
            "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files under a path in the sandbox. Args: path (optional)",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
        }
    },
]

# ---------- Helpers ----------
def clean_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            return "```".join(parts[1:-1]).strip()
        return text.strip("`")
    return text

def extract_first_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = clean_code_fence(text)
    start = text.find("{")
    if start == -1:
        return None
    for end in range(start + 1, min(len(text), start + 8000)):
        if text[end] == "}":
            cand = text[start:end+1]
            try:
                return json.loads(cand)
            except Exception:
                continue
    try:
        return json.loads(text)
    except Exception:
        return None

# Heuristic to find quoted content in user input
QUOTE_RE = re.compile(r'["\'](.*?)["\']')

def extract_user_provided_content(user_input: str) -> Optional[str]:
    if not user_input:
        return None
    m = QUOTE_RE.search(user_input)
    if m:
        return m.group(1).strip()
    patterns = [
        r'and write (?:a |the )?(?:simple )?(.*?)$',
        r'with content (.*?)$',
        r'write (.*?)$',
        r'contents?: (.*?)$',
    ]
    for pat in patterns:
        mm = re.search(pat, user_input, re.IGNORECASE)
        if mm:
            return mm.group(1).strip(' ."\'')
    return None

# ---------- Local fallback simulator (unchanged, small) ----------
def local_fallback_simulator(messages):
    last_user = None
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    if not last_user:
        content = json.dumps({"call":"assistant","message":"I am offline but ready to help."})
        return {"choices":[{"message":{"content": content}}]}
    lower = last_user.lower()
    if ("create file" in lower) or ("create" in lower and "file" in lower):
        user_content = extract_user_provided_content(last_user)
        wants_generate = "generate" in lower or "generate a" in lower
        mname = re.search(r'file\s+([A-Za-z0-9_\-\.]+)', last_user)
        filename = mname.group(1) if mname else "untitled.txt"
        if not user_content and wants_generate:
            if filename.endswith(".js"):
                generated = "console.log('Hello, world!');"
            elif filename.endswith(".py"):
                generated = "print('Hello, world!')"
            else:
                generated = "Hello, world!"
            args = {"filename": filename, "content": generated, "type": filename.split(".")[-1] if "." in filename else "text"}
        else:
            content_to_use = user_content or ""
            args = {"filename": filename, "content": content_to_use, "type": filename.split(".")[-1] if "." in filename else "text"}
        system_obj = {"call":"system","function":{"name":"createfile","args": args}}
        return {"choices":[{"message":{"content": json.dumps(system_obj)}}]}
    assistant_obj = {"call":"assistant","message":"(local fallback) I can't reach the API right now but here's a helpful reply."}
    return {"choices":[{"message":{"content": json.dumps(assistant_obj)}}]}

# ---------- Chat (retry + fallback) ----------
def chat_with_ai(messages, temperature: float = 0.2, timeout: int = 60, max_retries: int = 5):
    if not API_KEY:
        print("⚠️ OPENROUTER_API_KEY not set. Using local fallback simulator.")
        return local_fallback_simulator(messages)
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": messages, "temperature": temperature, "tools": TOOLS_SCHEMA, "tool_choice": "auto"}
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            if 200 <= r.status_code < 300:
                try:
                    return r.json()
                except Exception:
                    print("❌ Failed to parse JSON; using fallback.")
                    return local_fallback_simulator(messages)
            if r.status_code == 429:
                print(f"⚠️ Received 429 rate limit (attempt {attempt}/{max_retries}). Backing off...")
                sleep_for = min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5)
                time.sleep(sleep_for)
                continue
            if 500 <= r.status_code < 600:
                print(f"⚠️ Server error {r.status_code} (attempt {attempt}/{max_retries}). Retrying...")
                sleep_for = min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5)
                time.sleep(sleep_for)
                continue
            print(f"❌ OpenRouter returned status {r.status_code}. Body: {r.text}")
            return local_fallback_simulator(messages)
        except requests.RequestException as e:
            print(f"⚠️ Network error (attempt {attempt}/{max_retries}): {e}")
            time.sleep(min(30, (2 ** attempt) * 0.5) + random.uniform(0, 0.5))
            continue
    print("❌ Exhausted retries. Falling back to local simulator.")
    return local_fallback_simulator(messages)

# ---------- FIXED execute_tool_by_name ----------
def execute_tool_by_name(name: str, args: dict, user_input_content: Optional[str]) -> dict:
    """
    Normalize args and call the function from TOOL_REGISTRY.
    This carefully maps filename <-> path and passes only parameters the function accepts.
    """
    if not name:
        return {"ok": False, "error": "no function name provided"}
    func = TOOL_REGISTRY.get(name)
    if not func:
        return {"ok": False, "error": f"unknown function '{name}'"}
    
    # normalize common keys
    normalized = {}
    if isinstance(args, dict):
        for k, v in args.items():
            lk = k.lower()
            if lk in ("filename", "file", "path", "name"):
                normalized.setdefault("filename", v)
                normalized.setdefault("path", v)
            elif lk in ("content", "body"):
                normalized["content"] = v
            else:
                normalized[k] = v
    elif isinstance(args, str):
        normalized["content"] = args
    
    # fallback to user-provided content if model did not provide content and user did
    if "content" not in normalized and user_input_content:
        normalized["content"] = user_input_content
    
    # Inspect function signature and prepare kwargs that the function accepts
    sig = inspect.signature(func)
    func_kwargs = {}
    for param in sig.parameters:
        # supply filename/path/content if available
        if param in normalized:
            func_kwargs[param] = normalized[param]
    
    # If function accepts 'path' but we only have 'filename', map it
    if 'path' in sig.parameters and 'path' not in func_kwargs and 'filename' in normalized:
        func_kwargs['path'] = normalized['filename']
    if 'filename' in sig.parameters and 'filename' not in func_kwargs and 'path' in normalized:
        func_kwargs['filename'] = normalized['path']
    
    # Debug print: show exactly what we will call
    print("→ Executing local function:", func.__name__, "with kwargs:", func_kwargs)
    try:
        return func(**func_kwargs)
    except TypeError as e:
        # last-resort: try calling with the normalized dict as keyword args
        try:
            print("⚠️ TypeError calling with restricted kwargs; trying full normalized dict as kwargs.")
            return func(**normalized)
        except Exception as ex:
            return {"ok": False, "error": f"function call failed: {ex}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------- Main agent loop ----------
SYSTEM_INSTRUCTION = (
    "You MUST RESPOND with a single top-level JSON object only.\n"
    "If you want the integration to execute a tool, reply with: "
    '{"call":"system","function":{"name":"<tool_name>","args":{...}}}\n'
    "If no tool is needed, reply with: {\"call\":\"assistant\",\"message\":\"...\"}\n"
    "Supported tools: createfile (filename, content), read_file (filename), list_files (path).\n"
)

def main():
    print("OpenRouter JSON-agent (fixed mapping). Type 'quit' or 'exit'.")
    print("Files under:", BASE_DIR)
    messages = [{"role":"system","content": SYSTEM_INSTRUCTION}]
    
    while True:
        try:
            usr = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not usr:
            continue
        if usr.lower() in ("quit", "exit"):
            print("Bye.")
            break
        
        user_provided_content = extract_user_provided_content(usr)
        messages.append({"role":"user","content": usr})
        resp = chat_with_ai(messages)
        
        if not resp:
            print("No response.")
            continue
        
        tool_calls = resp.get("tool_calls") or []
        assistant_raw = ""
        choices = resp.get("choices", [])
        if choices:
            assistant_raw = choices[0].get("message", {}).get("content") or ""
            if not tool_calls:
                tool_calls = choices[0].get("message", {}).get("tool_calls") or []
        
        if tool_calls:
            tc = tool_calls[0]
            func_name = tc.get("function", {}).get("name") or tc.get("name") or tc.get("function_name")
            params = tc.get("function", {}).get("arguments") or tc.get("function", {}).get("parameters") or tc.get("arguments") or tc.get("parameters") or {}
            
            # FIX: Parse arguments if it's a JSON string
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse arguments as JSON: {params}")
                    params = {}
            
            if not func_name:
                print("Malformed tool_calls:", tc)
                messages.append({"role":"assistant","content":"Error: malformed tool_calls"})
                continue
            
            print(f"Model requested tool: {func_name} with args: {params}")
            result = execute_tool_by_name(func_name, params or {}, user_provided_content)
            messages.append({"role":"function","name":func_name,"content": json.dumps(result)})
            user_action = {"call":"user","action": {func_name: "success" if result.get("ok") else "error", "filename": result.get("filename",""), "detail": result.get("message") or result.get("error","")}}
            messages.append({"role":"user","content": json.dumps(user_action)})
            
            if result.get("ok"):
                print(f"✅ Tool succeeded: {result.get('filename')}  ({result.get('message')})")
            else:
                print(f"❌ Tool failed: {result.get('error')}")
            
            follow = chat_with_ai(messages)
            if not follow:
                print("No follow-up.")
                continue
            
            choices2 = follow.get("choices", [])
            if choices2:
                final_content = choices2[0].get("message", {}).get("content") or ""
                parsed = extract_first_json(final_content)
                if parsed:
                    print("\n🤖 AI (json):", json.dumps(parsed, indent=2))
                else:
                    print("\n🤖 AI:", final_content.strip())
                messages.append({"role":"assistant","content": final_content})
            continue
        
        assistant_text = assistant_raw or (choices[0].get("message", {}).get("content") if choices else "")
        parsed = extract_first_json(assistant_text)
        
        if parsed and isinstance(parsed, dict) and parsed.get("call") == "system" and parsed.get("function"):
            func = parsed["function"]
            func_name = func.get("name")
            args = func.get("args") or {}
            
            # FIX: Parse args if it's a JSON string
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse args as JSON: {args}")
                    args = {}
            
            print(f"(fallback) Model requested function: {func_name} args={args}")
            result = execute_tool_by_name(func_name, args, user_provided_content)
            messages.append({"role":"function","name":func_name,"content": json.dumps(result)})
            user_action = {"call":"user","action": {func_name: "success" if result.get("ok") else "error", "filename": result.get("filename",""), "detail": result.get("message") or result.get("error","")}}
            messages.append({"role":"user","content": json.dumps(user_action)})
            
            if result.get("ok"):
                print(f"✅ Tool succeeded: {result.get('filename')}  ({result.get('message')})")
            else:
                print(f"❌ Tool failed: {result.get('error')}")
            
            follow = chat_with_ai(messages)
            if not follow:
                print("No follow-up.")
                continue
            
            final = follow.get("choices", [])[0].get("message", {}).get("content", "")
            parsed_final = extract_first_json(final)
            if parsed_final:
                print("\n🤖 AI (json):", json.dumps(parsed_final, indent=2))
            else:
                print("\n🤖 AI:", final.strip())
            messages.append({"role":"assistant","content": final})
            continue
        
        if parsed and isinstance(parsed, dict) and parsed.get("call") == "assistant":
            print("\n🤖 AI (assistant json):", json.dumps(parsed, indent=2))
            messages.append({"role":"assistant","content": json.dumps(parsed)})
        else:
            raw = assistant_text or json.dumps(resp)
            print("\n🤖 AI:", raw.strip())
            messages.append({"role":"assistant","content": raw})

if __name__ == "__main__":
    main()