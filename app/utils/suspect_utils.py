





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
# from google.genai import types
# from openai import OpenAI
# from tavily import TavilyClient

# # --- UPDATED AI CONFIGURATION ---
# gemini_client = None
# if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "YOUR_API_KEY_HERE":
#     try:
#         gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
#     except Exception as e:
#         print(f"Error initializing Gemini client: {e}")
# # --------------------------------

# openai_client = None
# if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "YOUR_API_KEY_HERE":
#     openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def extract_artifacts(text: str) -> dict:
#     print(f"\n[TOOL CALLED] Running `extract_artifacts`...")
#     artifacts = {}
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
#     print(f"\n[TOOL CALLED] Running `inspect_urls` for {len(urls)} URLs...")
#     if not urls: 
#         print("[TOOL SKIPPED] No URLs provided.")
#         return []
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
#     print(f"[TOOL RESULT] URL inspection complete. {len(results)} records created.")
#     return results

# def inspect_ips(ips: list) -> list:
#     print(f"\n[TOOL CALLED] Running `inspect_ips` for {len(ips)} IPs...")
#     if not ips:
#         print("[TOOL SKIPPED] No IPs provided.")
#         return []
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
#     print(f"[TOOL RESULT] IP inspection complete. {len(results)} records created.")
#     return results

# TOOL_REGISTRY = {
#     "extract_artifacts": extract_artifacts,
#     "inspect_urls": inspect_urls,
#     "inspect_ips": inspect_ips,
# }

# # --- TOOL DECLARATIONS FOR GEMINI FUNCTION CALLING ---
# TOOL_DECLARATIONS = [
#     types.FunctionDeclaration(
#         name="extract_artifacts",
#         description="Extracts digital artifacts (emails, URLs, IPs) from text. Use this to find data points in the evidence for further investigation.",
#         parameters=types.Schema(
#             type=types.Type.OBJECT,
#             properties={
#                 "text": types.Schema(
#                     type=types.Type.STRING,
#                     description="The text evidence to extract artifacts from."
#                 )
#             },
#             required=["text"]
#         )
#     ),
#     types.FunctionDeclaration(
#         name="inspect_urls",
#         description="Performs DNS and WHOIS lookups on a list of URLs for investigation. Only call this if URLs were found by extract_artifacts.",
#         parameters=types.Schema(
#             type=types.Type.OBJECT,
#             properties={
#                 "urls": types.Schema(
#                     type=types.Type.ARRAY,
#                     description="List of URLs to investigate.",
#                     items=types.Schema(type=types.Type.STRING)
#                 )
#             },
#             required=["urls"]
#         )
#     ),
#     types.FunctionDeclaration(
#         name="inspect_ips",
#         description="Performs RDAP lookups on a list of IP addresses to find ownership and location. Only call this if IPs were found by extract_artifacts.",
#         parameters=types.Schema(
#             type=types.Type.OBJECT,
#             properties={
#                 "ips": types.Schema(
#                     type=types.Type.ARRAY,
#                     description="List of IP addresses to investigate.",
#                     items=types.Schema(type=types.Type.STRING)
#                 )
#             },
#             required=["ips"]
#         )
#     ),
# ]
# # ---------------------------------------------------

# def analyze_evidence(text: str = "", file_path: str = None):
#     print("\n--- [START] New GEMINI-DRIVEN Forensic Analysis ---")
#     if not gemini_client:
#         return {"summary": "Gemini AI client not configured.", "suspect_profile": "Unknown", "evidence_log": ["AI client not configured."]}

#     # UPDATED: Non-prescriptive prompt - AI decides when to call extract_artifacts
#     SYSTEM_PROMPT = (
#         "You are a forensic investigation agent. Your primary goal is to provide a final, comprehensive summary of a cybercrime incident and the suspected profile. Follow these steps:\n"
#         "1. **Analysis Strategy:** First, use the `extract_artifacts` tool on the evidence text to find digital clues (URLs, IPs, Emails).\n"
#         "2. **Deep Dive:** If clues are found, use the appropriate `inspect_urls` and `inspect_ips` tools to gather more information on the indicators of compromise.\n"
#         "3. **Synthesize & Conclude:** Once all necessary tool results are available, synthesize the findings to create a detailed final summary and determine the likely suspect profile. Your final response MUST be a detailed text summary, not a function call."
#     )

#     # Initialize conversation history with System and User prompts
#     messages = [
#         types.Content(role="system", parts=[types.Part.from_text(SYSTEM_PROMPT)]),
#         types.Content(role="user", parts=[types.Part.from_text(f"Analyze this cybercrime evidence:\n\n{text}")]),
#     ]

#     tool_results = []

#     for turn in range(5): 
#         try:
#             response = gemini_client.models.generate_content(
#                 model='gemini-2.5-flash',
#                 contents=messages,
#                 config=types.GenerateContentConfig(
#                     tools=TOOL_DECLARATIONS
#                 )
#             )
#         except Exception as e:
#             print(f"AI API Error: {e}")
#             return {"summary": f"AI API Error: {e}", "suspect_profile": "Unknown", "tool_results": tool_results}

#         # Check for function calls
#         if response.function_calls:
#             print(f"[AI TURN {turn+1}] AI requested {len(response.function_calls)} tool call(s).")

#             # Append the AI's function call request to the history
#             messages.append(response.candidates[0].content)

#             # Prepare and execute tool calls
#             function_responses = []
#             for function_call in response.function_calls:
#                 func_name = function_call.name
#                 func_args = dict(function_call.args)
#                 print(f"  → Executing tool: `{func_name}` with args: {func_args}")

#                 if func_name in TOOL_REGISTRY:
#                     tool_func = TOOL_REGISTRY[func_name]
#                     try:
#                         tool_output = tool_func(**func_args)
#                         # Only record tool output if it's not a skip due to no data
#                         if tool_output is not None:
#                             tool_results.append({"tool": func_name, "args": func_args, "output": tool_output})

#                         function_responses.append(
#                             types.Part.from_function_response(
#                                 name=func_name,
#                                 response={
#                                     "result": tool_output if tool_output is not None else {"status": "skipped", "reason": "No data provided"}
#                                 }
#                             )
#                         )
#                     except Exception as e:
#                         print(f"  ❌ Tool execution failed: {e}")
#                         function_responses.append(
#                             types.Part.from_function_response(
#                                 name=func_name,
#                                 response={
#                                     "result": {"error": str(e)}
#                                 }
#                             )
#                         )

#             # Send the tool responses back to the model
#             if function_responses:
#                 messages.append(
#                     types.Content(role="tool", parts=function_responses)
#                 )

#         # If no function call, the model is providing the final text answer
#         elif response.text:
#             print(f"[AI TURN {turn+1}] AI provided final text summary.")
#             final_summary_text = response.text.strip()
            
#             # Extract initial artifacts from tool_results for the dashboard view
#             initial_artifacts = {}
#             for res in tool_results:
#                 if res['tool'] == 'extract_artifacts':
#                     initial_artifacts = res['output']
#                     break

#             return {
#                 "summary": final_summary_text,
#                 "suspect_profile": "AI Generated (See Summary)",
#                 "clues": [],
#                 "artifacts": initial_artifacts,
#                 "tool_results": tool_results
#             }

#         else:
#             print(f"[AI TURN {turn+1}] Unexpected AI response format.")
#             return {"summary": "AI returned an empty or malformed response.", "suspect_profile": "Inconclusive", "tool_results": tool_results}

#     return {"summary": "Analysis reached maximum turns without a final answer.", "suspect_profile": "Inconclusive", "tool_results": tool_results}

# def web_search(query: str) -> dict:
#     print(f"\n[TOOL CALLED] Running `web_search` for query: {query}...")
#     try:
#         api_key = os.getenv("TAVILY_API_KEY")
#         if not api_key:
#             return {"error": "Tavily API key is not configured."}
#         tavily = TavilyClient(api_key=api_key)
#         response = tavily.search(query=query, search_depth="basic", max_results=3)
#         return {"results": response['results']}
#     except Exception as e:
#         print(f"[TOOL ERROR] Tavily search failed: {e}")
#         return {"error": str(e)}




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
from tavily import TavilyClient

# NEW: Configure only for the single-key guidance route if needed, 
# but the main agent will use the multi-key logic in gemini_agent.py
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
    print(f"\n[TOOL CALLED] Running `inspect_urls` for {len(urls)} URLs...")
    if not urls or not isinstance(urls, list): 
        print("[TOOL SKIPPED] No URLs provided or invalid input.")
        return []
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
    print(f"[TOOL RESULT] URL inspection complete. {len(results)} records created.")
    return results

def inspect_ips(ips: list) -> list:
    print(f"\n[TOOL CALLED] Running `inspect_ips` for {len(ips)} IPs...")
    if not ips or not isinstance(ips, list):
        print("[TOOL SKIPPED] No IPs provided or invalid input.")
        return []
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
    print(f"[TOOL RESULT] IP inspection complete. {len(results)} records created.")
    return results

def web_search(query: str) -> dict:
    print(f"\n[TOOL CALLED] Running `web_search` for query: {query}...")
    if not query:
        print("[TOOL SKIPPED] Empty query provided.")
        return {"results": []}
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

TOOL_REGISTRY = {
    "extract_artifacts": extract_artifacts,
    "inspect_urls": inspect_urls,
    "inspect_ips": inspect_ips,
    "web_search": web_search, # NEW TOOL
}


def chat_with_ai(messages):
    # This function is not used in the new stateless architecture but remains for compatibility
    pass

# --- OLD analyze_evidence function updated to call the new agent ---
def analyze_evidence(text: str = "", file_path: str = None):
    from app.utils.gemini_agent import run_analysis_agent # Import the new gemini agent
    print("\n--- [START] AI-DRIVEN Forensic Analysis (Wrapper) ---")
    
    # Assemble minimal context for the agent
    context = f"## EVIDENCE DESCRIPTION\n{text}\n## EVIDENCE FILE PATH\n{file_path or 'No file provided'}"
    
    raw_findings = run_analysis_agent(text_to_analyze=context, report_id=0, file_path=file_path)
    
    # Simple reformatting for the old analyze_evidence return format
    initial_artifacts = {}
    for tool_run in raw_findings.get("tool_results", []):
        if tool_run.get("tool") == "extract_artifacts":
            initial_artifacts = tool_run.get("output", {})
            break
            
    return {
        "summary": raw_findings.get("final_summary_text", "Analysis complete."),
        "suspect_profile": "AI Generated (See Summary)",
        "clues": [],
        "artifacts": initial_artifacts,
        "tool_results": raw_findings.get("tool_results", [])
    }