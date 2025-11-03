# # app/utils/gemini_helper.py
# import google.generativeai as genai
# import os
# from app.utils.classifier import classify_incident

# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# model = genai.GenerativeModel("gemini-1.5-flash") 

# def get_guidance(text):
    
#     category = classify_incident(text)

#     prompt = f"""
#     A user has reported a cybercrime.
#     Category: {category}
#     Description: {text}

#     Please provide:
#     1. Next steps for the victim
#     2. Relevant legal sections (India)
#     3. Where to report officially
#     Return concise guidance in JSON format.
#     """

#     response = model.generate_content(prompt)
#     return {
#         "category": category,
#         "guidance": response.text if response and response.text else "No response"
#     }

# def guess_suspect(text):
#     prompt = f"""
#     Analyze the following report/evidence:
#     {text}

#     Identify possible suspect characteristics or technical clues 
#     (e.g., spoofing, phishing style, fraud patterns, IP hints).
#     Return structured JSON.
#     """
#     response = model.generate_content(prompt)
#     return response.text if response and response.text else "No response"




import google.generativeai as genai
import os
from app.utils.classifier import classify_text
from google.genai import types

# --- UPDATED AI CONFIGURATION ---
client = None
try:
    if os.getenv("GOOGLE_API_KEY"):
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
# --------------------------------


def get_guidance(text):
    if not client:
        return {"category": "Unknown", "guidance": "Gemini AI service is not configured correctly on the server."}

    prompt = (
        "You are an expert Indian cybercrime legal assistant. "
        "Based on the following user query, provide clear, concise, and actionable guidance. "
        "Explain the type of cybercrime, immediate steps the user should take, "
        "what evidence to collect, and which sections of Indian law might apply. "
        "Keep the tone helpful and reassuring.\n\n"
        f"User Query: \"{text}\""
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        return {
            "category": classify_text(text).get("category") if text else "Unknown",
            "guidance": response.text if response and response.text else "No response"
        }
    except Exception as e:
        print(f"Gemini guidance error: {e}")
        return {
            "category": "Unknown",
            "guidance": f"The AI guidance service failed: {str(e)}"
        }

def guess_suspect(text):
    # This function is deprecated, the real analysis is in suspect_utils.analyze_evidence
    response = "The dedicated forensic AI agent is running the analysis in the background using advanced tools. Check the Report Details for the full output."
    return response if response else "No response"