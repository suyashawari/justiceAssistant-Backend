
# import re
# import os
# import socket
# import hashlib
# import json
# import tldextract
# import whois
# import dns.resolver
# from ipwhois import IPWhois
# import google.generativeai as genai
# from openai import OpenAI

# # --- AI Configuration ---
# # Initialize clients if valid API keys are provided.
# gemini_model = None
# if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "YOUR_API_KEY_HERE":
#     genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
#     gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# openai_client = None
# if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "YOUR_API_KEY_HERE":
#     openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# # ------------------------

# # ==============================================================================
# #  SECTION 1: THE "TOOLS" THE AI CAN USE
# #  These are your original functions, now acting as tools for the AI agent.
# #  We add print statements so we can see when the AI chooses to use them.
# # ==============================================================================

# def extract_artifacts(text: str) -> dict:
#     """Extracts potential artifacts (emails, URLs, IPs) from a given block of text."""
#     print(f"\n[TOOL CALLED] Running `extract_artifacts`...")
#     artifacts = {}
#     # (The internal logic of this function is unchanged)
#     emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
#     if emails: artifacts["emails"] = list(dict.fromkeys(emails))
#     urls = re.findall(r"http[s]?://[^\s'\"<>]+", text)
#     if urls: artifacts["urls"] = list(dict.fromkeys(urls))
#     ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
#     valid_ips = [ip for ip in ips if all(0 <= int(p) <= 255 for p in ip.split("."))]
#     if valid_ips: artifacts["ips"] = list(dict.fromkeys(valid_ips))
#     print(f"[TOOL RESULT] Found artifacts: {list(artifacts.keys())}")
#     return artifacts

# def inspect_urls(urls: list) -> list:
#     """Performs DNS and WHOIS lookups on a list of URLs to gather intelligence."""
#     print(f"\n[TOOL CALLED] Running `inspect_urls` for {urls}...")
#     results = []
#     if not isinstance(urls, list): return [{"error": "Input must be a list of URLs."}]
#     for url in urls:
#         entry = {"url": url}
#         try:
#             ext = tldextract.extract(url)
#             domain = f"{ext.domain}.{ext.suffix}"
#             entry["domain"] = domain
#             try:
#                 answers = dns.resolver.resolve(domain, "A")
#                 entry["dns_resolved_ips"] = [r.to_text() for r in answers]
#             except Exception as e:
#                 entry["dns_error"] = str(e)
#             try:
#                 w = whois.whois(domain)
#                 entry["whois_registrar"] = w.registrar
#                 entry["whois_creation_date"] = str(w.creation_date)
#             except Exception as e:
#                 entry["whois_error"] = str(e)
#         except Exception as e:
#             entry["error"] = str(e)
#         results.append(entry)
#     print(f"[TOOL RESULT] URL inspection complete.")
#     return results

# def inspect_ips(ips: list) -> list:
#     """Performs RDAP lookups on a list of IP addresses."""
#     print(f"\n[TOOL CALLED] Running `inspect_ips` for {ips}...")
#     results = []
#     if not isinstance(ips, list): return [{"error": "Input must be a list of IPs."}]
#     for ip in ips:
#         entry = {"ip": ip}
#         try:
#             obj = IPWhois(ip)
#             rd = obj.lookup_rdap()
#             entry["asn_description"] = rd.get("asn_description")
#             entry["country"] = rd.get("country")
#         except Exception as e:
#             entry["error"] = str(e)
#         results.append(entry)
#     print(f"[TOOL RESULT] IP inspection complete.")
#     return results

# # ==============================================================================
# #  SECTION 2: THE AI AGENT'S CORE LOGIC
# #  This is the new part that manages the conversation with the AI.
# # ==============================================================================

# TOOL_REGISTRY = {
#     "extract_artifacts": extract_artifacts,
#     "inspect_urls": inspect_urls,
#     "inspect_ips": inspect_ips,
# }

# SYSTEM_PROMPT = """You are a highly skilled cyber forensic analyst agent. Your goal is to analyze a user-provided report to identify potential suspects and gather intelligence.

# You have access to a toolbox of functions. You must decide which tools to use and in what order.

# Here are the tools available:
# - `extract_artifacts(text: str)`: Use this FIRST to find emails, URLs, and IPs in the initial report.
# - `inspect_urls(urls: list)`: Use this on the URLs you found to get DNS and WHOIS info.
# - `inspect_ips(ips: list)`: Use this on the IPs you found to get network owner information.

# Your workflow is a conversation. At each step, you can either call a tool or provide a final answer.
# - To call a tool, respond ONLY with a single JSON object like this:
#   `{"tool_name": "function_name", "arguments": {"arg_name": "value"}}`
# - After I run the tool for you, I will give you the result.
# - Use the tool results to decide your next step. You can call another tool or formulate your final conclusion.

# When you have gathered enough information and are ready to conclude, provide your final analysis as a single JSON object with the keys "summary", "suspect_profile", and "evidence_log". The "evidence_log" should be a list of strings describing the steps you took. Do not call any more tools in your final answer.
# """

# def chat_with_ai(messages):
#     """Sends messages to the AI and gets a response. Prefers Gemini."""
#     if gemini_model:
#         print("\n[AI TURN] Sending context to Google Gemini...")
#         response = gemini_model.generate_content(messages)
#         return response.text
#     elif openai_client:
#         print("\n[AI TURN] Sending context to OpenAI...")
#         response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
#         return response.choices[0].message.content
#     else:
#         return json.dumps({"summary": "No AI model available.", "suspect_profile": "Unknown", "evidence_log": ["AI client not configured."]})

# def analyze_evidence(text: str = "", file_path: str = None):
#     """
#     The new AI-driven agent orchestrator.
#     Manages a multi-turn conversation with the AI to perform analysis.
#     """
#     print("\n--- [START] New AI-DRIVEN Forensic Analysis ---")
    
#     # We ignore file_path for now to simplify, but you could add a tool for it later.
    
#     messages = [
#         {"role": "user", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": f"Here is the cybercrime report to analyze:\n\n{text}"}
#     ]

#     # Limit the number of turns to prevent infinite loops
#     for _ in range(5): 
#         ai_response_text = chat_with_ai(messages)
        
#         # Add the AI's raw response to the message history
#         messages.append({"role": "model", "content": ai_response_text})

#         # Try to parse the response as a JSON object
#         try:
#             response_json = json.loads(ai_response_text)
            
#             # Check if it's a tool call
#             if "tool_name" in response_json and "arguments" in response_json:
#                 tool_name = response_json["tool_name"]
#                 args = response_json["arguments"]
                
#                 if tool_name in TOOL_REGISTRY:
#                     tool_function = TOOL_REGISTRY[tool_name]
                    
#                     # Execute the tool
#                     tool_result = tool_function(**args)
                    
#                     # Add the tool's result to the conversation for the AI's next turn
#                     messages.append({"role": "user", "content": f"Tool `{tool_name}` output:\n{json.dumps(tool_result)}"})
#                     continue # Go to the next loop to let the AI process the tool result
#                 else:
#                     messages.append({"role": "user", "content": f"Error: Tool '{tool_name}' not found."})
#                     continue

#             # If it's not a tool call, assume it's the final answer
#             print("[AI-DRIVEN] AI has provided a final answer. Analysis complete.")
#             return response_json

#         except (json.JSONDecodeError, TypeError):
#             # If the response is not valid JSON, it's a plain text final answer.
#             print("[AI-DRIVEN] AI provided a non-JSON final answer. Wrapping it.")
#             return {"summary": ai_response_text, "suspect_profile": "AI Generated", "evidence_log": ["AI provided a direct text answer."]}
            
#     print("[AI-DRIVEN] Reached maximum turns. Returning final result.")
#     return {"summary": "Analysis reached maximum turns.", "suspect_profile": "Inconclusive", "evidence_log": messages}


import re
import os
import socket
import hashlib
import json
import tldextract
import whois
import dns.resolver
from ipwhois import IPWhois
import google.generativeai as genai
from openai import OpenAI
from tavily import TavilyClient # <-- Import TavilyClient

gemini_model = None
if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "YOUR_API_KEY_HERE":
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

openai_client = None
if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "YOUR_API_KEY_HERE":
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_artifacts(text: str) -> dict:
    print(f"\n[TOOL CALLED] Running `extract_artifacts`...")
    artifacts = {}
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if emails: artifacts["emails"] = list(dict.fromkeys(emails))
    urls = re.findall(r"http[s]?://[^\s'\"<>]+", text)
    if urls: artifacts["urls"] = list(dict.fromkeys(urls))
    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    valid_ips = [ip for ip in ips if all(0 <= int(p) <= 255 for p in ip.split("."))]
    if valid_ips: artifacts["ips"] = list(dict.fromkeys(valid_ips))
    print(f"[TOOL RESULT] Found artifacts: {list(artifacts.keys())}")
    return artifacts


def inspect_urls(urls: list) -> list:
    print(f"\n[TOOL CALLED] Running `inspect_urls` for {urls}...")
    results = []
    if not isinstance(urls, list): return [{"error": "Input must be a list of URLs."}]
    for url in urls:
        entry = {"url": url}
        try:
            ext = tldextract.extract(url)
            domain = f"{ext.domain}.{ext.suffix}"
            entry["domain"] = domain
            try:
                answers = dns.resolver.resolve(domain, "A")
                entry["dns_resolved_ips"] = [r.to_text() for r in answers]
            except Exception as e:
                entry["dns_error"] = str(e)
            try:
                w = whois.whois(domain)
                entry["whois_registrar"] = w.registrar
                entry["whois_creation_date"] = str(w.creation_date)
            except Exception as e:
                entry["whois_error"] = str(e)
        except Exception as e:
            entry["error"] = str(e)
        results.append(entry)
    print(f"[TOOL RESULT] URL inspection complete.")
    return results


def inspect_ips(ips: list) -> list:
    print(f"\n[TOOL CALLED] Running `inspect_ips` for {ips}...")
    results = []
    if not isinstance(ips, list): return [{"error": "Input must be a list of IPs."}]
    for ip in ips:
        entry = {"ip": ip}
        try:
            obj = IPWhois(ip)
            rd = obj.lookup_rdap()
            entry["asn_description"] = rd.get("asn_description")
            entry["country"] = rd.get("country")
        except Exception as e:
            entry["error"] = str(e)
        results.append(entry)
    print(f"[TOOL RESULT] IP inspection complete.")
    return results

TOOL_REGISTRY = {
    "extract_artifacts": extract_artifacts,
    "inspect_urls": inspect_urls,
    "inspect_ips": inspect_ips,
}

def chat_with_ai(messages):
    if gemini_model:
        print("\n[AI TURN] Sending context to Google Gemini...")
        response = gemini_model.generate_content(messages)
        return response.text
    elif openai_client:
        print("\n[AI TURN] Sending context to OpenAI...")
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content
    else:
        return json.dumps({"summary": "No AI model available.", "suspect_profile": "Unknown", "evidence_log": ["AI client not configured."]})

def analyze_evidence(text: str = "", file_path: str = None):
    print("\n--- [START] New AI-DRIVEN Forensic Analysis ---")
    SYSTEM_PROMPT = "You are an AI assistant. Analyze the evidence, call tools if needed, and provide a summary."
    messages = [
        {"role": "user", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is the cybercrime report to analyze:\n\n{text}"}
    ]
    for _ in range(5):
        ai_response_text = chat_with_ai(messages)
        messages.append({"role": "model", "content": ai_response_text})
        try:
            response_json = json.loads(ai_response_text)
            if "tool_name" in response_json and "arguments" in response_json:
                tool_name = response_json["tool_name"]
                args = response_json["arguments"]
                if tool_name in TOOL_REGISTRY:
                    tool_function = TOOL_REGISTRY[tool_name]
                    tool_result = tool_function(**args)
                    messages.append({"role": "user", "content": f"Tool `{tool_name}` output:\n{json.dumps(tool_result)}"})
                    continue
                else:
                    messages.append({"role": "user", "content": f"Error: Tool '{tool_name}' not found."})
                    continue
            print("[AI-DRIVEN] AI has provided a final answer. Analysis complete.")
            return response_json
        except (json.JSONDecodeError, TypeError):
            print("[AI-DRIVEN] AI provided a non-JSON final answer. Wrapping it.")
            return {"summary": ai_response_text, "suspect_profile": "AI Generated", "evidence_log": ["AI provided a direct text answer."]}
    print("[AI-DRIVEN] Reached maximum turns. Returning final result.")
    return {"summary": "Analysis reached maximum turns.", "suspect_profile": "Inconclusive", "evidence_log": messages}

# --- NEW FUNCTION ADDED HERE ---
def web_search(query: str) -> dict:
    """
    Performs a web search using the Tavily API to find relevant information.
    """
    print(f"\n[TOOL CALLED] Running `web_search` for query: {query}...")
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"error": "Tavily API key is not configured."}
        
        tavily = TavilyClient(api_key=api_key)
        
        response = tavily.search(query=query, search_depth="basic", max_results=3)
        
        return {"results": response['results']}

    except Exception as e:
        print(f"[TOOL ERROR] Tavily search failed: {e}")
        return {"error": str(e)}