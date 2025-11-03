# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# import openai
# from app.models import db
# from app.models.models import Report
# from werkzeug.utils import secure_filename
# from app.utils.suspect_utils import analyze_evidence

# load_dotenv()

# gemini_key = os.getenv("GOOGLE_API_KEY")
# openai_key = os.getenv("OPENAI_API_KEY")

# if gemini_key:
#     genai.configure(api_key=gemini_key)

# if openai_key:
#     openai.api_key = openai_key

# ai = Blueprint('ai', __name__)
# UPLOAD_FOLDER = "uploads"

# # --------- GET GUIDANCE ----------
# @ai.route('/get-guidance', methods=['POST'])
# @jwt_required()
# def get_guidance():
#     data = request.get_json()
#     user_query = data.get("query", "")

#     if not user_query:
#         return jsonify({"status": "error", "error": "Query is required"}), 400

#     prompt = f"""
#     You are a cybercrime assistant. A user submitted this incident: 
#     \"{user_query}\"

#     Based on this, give:
#     - Personalized and practical steps they should take
#     - Safety tips based on the context
#     - Relevant official links or contacts (if applicable)

#     Keep it short, clear, and victim-friendly.
#     """

#     # 1️⃣ Try Gemini
#     if gemini_key:
#         try:
#             model = genai.GenerativeModel("gemini-1.5-flash")
#             response = model.generate_content(prompt)
#             guidance_text = getattr(response, "text", None)

#             if not guidance_text and hasattr(response, "candidates"):
#                 guidance_text = response.candidates[0].content.parts[0].text

#             if guidance_text:
#                 return jsonify({
#                     "status": "success",
#                     "provider": "Gemini",
#                     "guidance": guidance_text
#                 }), 200
#         except Exception as e:
#             print(f"Gemini failed: {e}")

#     # 2️⃣ Fallback to OpenAI
#     if openai_key:
#         try:
#             completion = openai.ChatCompletion.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful cybercrime reporting assistant."},
#                     {"role": "user", "content": prompt}
#                 ]
#             )
#             guidance_text = completion.choices[0].message["content"]
#             return jsonify({
#                 "status": "success",
#                 "provider": "OpenAI",
#                 "guidance": guidance_text
#             }), 200
#         except Exception as e:
#             print(f"OpenAI failed: {e}")

#     # 3️⃣ If both fail
#     return jsonify({
#         "status": "error",
#         "error": "Both Gemini and OpenAI services failed. Please try again later."
#     }), 500


# # --------- SUSPECT GUESS ----------
# @ai.route('/guess-suspect', methods=['POST'])
# @jwt_required()
# def guess_suspect():
#     user_id = get_jwt_identity()

#     data = request.form.to_dict() or {}
#     report_id = data.get("report_id")  # may be None
#     evidence_text = data.get("evidence_text", "")
#     evidence_file = request.files.get("evidence_file")

#     file_path = None

#     if report_id:
#         # Fetch report from DB
#         report = Report.query.filter_by(id=report_id, user_id=user_id).first()
#         if not report:
#             return jsonify({"status": "error", "error": "Report not found"}), 404
#         evidence_text = report.description
#         file_path = report.evidence_file

#     elif evidence_file:
#         # Save uploaded file temporarily
#         os.makedirs("uploads", exist_ok=True)
#         filename = secure_filename(evidence_file.filename)
#         file_path = os.path.join("uploads", filename)
#         evidence_file.save(file_path)

#     if not evidence_text and not file_path:
#         return jsonify({
#             "status": "error",
#             "error": "Either text or file evidence is required"
#         }), 400

#     # Run forensic analysis
#     result = analyze_evidence(text=evidence_text, file_path=file_path)

#     # Dashboard-friendly summary
#     dashboard_view = {
#         "suspect_profile": result.get("suspect_profile") or "Unknown",
#         "summary": result.get("summary", ""),
#         "artifacts": {
#             "emails": result.get("artifacts", {}).get("emails", []),
#             "urls": result.get("artifacts", {}).get("urls", []),
#             "ip_addresses": result.get("artifacts", {}).get("ips", []),
#         }
#     }

#     # Detailed view
#     detailed_view = {
#         "summary": result.get("summary", ""),
#         "suspect_profile": result.get("suspect_profile") or "Unknown",
#         "clues": result.get("clues", []),
#         "artifacts": result.get("artifacts", {}),
#         "tool_results": {
#             "whois": result.get("whois", {}),
#             "dns": result.get("dns", {}),
#             "ip_info": result.get("ip_info", {}),
#             "url_analysis": result.get("url_analysis", {}),
#             "file_metadata": result.get("file_metadata", {})
#         }
#     }

#     return jsonify({
#         "status": "success",
#         "dashboard": dashboard_view,
#         "detailed": detailed_view
#     }), 200




from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests  # <-- Import the requests library
from dotenv import load_dotenv
from app.models import db
from app.models.models import Report
from werkzeug.utils import secure_filename
from app.utils.suspect_utils import analyze_evidence

load_dotenv()

# --- MODIFIED: Use OpenRouter configuration ---
openrouter_key = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using a capable and free model available on OpenRouter
MODEL = "openai/gpt-oss-20b:free"
# --- END OF MODIFICATION ---

ai = Blueprint('ai', __name__)

UPLOAD_FOLDER = "uploads"

@ai.route('/get-guidance', methods=['POST'])
@jwt_required()
def get_guidance():
    data = request.get_json()
    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"status": "error", "error": "Query is required"}), 400

    # The prompt remains the same, providing context to the model
    prompt = (
        "You are an expert Indian cybercrime legal assistant. "
        "Based on the following user query, provide clear, concise, and actionable guidance. "
        "Explain the type of cybercrime, immediate steps the user should take, "
        "what evidence to collect, and which sections of Indian law might apply. "
        "Keep the tone helpful and reassuring.\n\n"
        f"User Query: \"{user_query}\""
    )

    # --- REWRITTEN: Logic to call OpenRouter API ---
    if not openrouter_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env file.")
        return jsonify({
            "status": "error",
            "error": "AI service is not configured correctly on the server."
        }), 500

    try:
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                # The system message is now part of the main prompt for simplicity,
                # but you could also separate it like this:
                # {"role": "system", "content": "You are an expert Indian cybercrime legal assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        
        # This will raise an exception for HTTP error codes (4xx or 5xx)
        response.raise_for_status() 

        response_data = response.json()
        guidance_text = response_data['choices'][0]['message']['content']

        return jsonify({
            "status": "success",
            "provider": f"OpenRouter ({MODEL})",
            "guidance": guidance_text
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API request failed: {e}")
        # Check if the error is due to an invalid key
        if e.response and e.response.status_code in [401, 403]:
            return jsonify({"status": "error", "error": "AI service authentication failed. Check server API key."}), 500
    except Exception as e:
        print(f"An error occurred while processing the OpenRouter response: {e}")

    return jsonify({
        "status": "error",
        "error": "The AI guidance service failed. Please try again later."
    }), 500
    # --- END OF REWRITE ---


@ai.route('/guess-suspect', methods=['POST'])
@jwt_required()
def guess_suspect():
    user_id = get_jwt_identity()
    data = request.form.to_dict() or {}
    report_id = data.get("report_id")
    evidence_text = data.get("evidence_text", "")
    evidence_file = request.files.get("evidence_file")

    file_path = None
    if report_id:
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        if not report:
            return jsonify({"status": "error", "error": "Report not found"}), 404
        evidence_text = report.description
        file_path = report.evidence_file
    elif evidence_file:
        os.makedirs("uploads", exist_ok=True)
        filename = secure_filename(evidence_file.filename)
        file_path = os.path.join("uploads", filename)
        evidence_file.save(file_path)

    if not evidence_text and not file_path:
        return jsonify({
            "status": "error",
            "error": "Either text or file evidence is required"
        }), 400

    result = analyze_evidence(text=evidence_text, file_path=file_path)

    dashboard_view = {
        "suspect_profile": result.get("suspect_profile") or "Unknown",
        "summary": result.get("summary", ""),
        "artifacts": {
            "emails": result.get("artifacts", {}).get("emails", []),
            "urls": result.get("artifacts", {}).get("urls", []),
            "ip_addresses": result.get("artifacts", {}).get("ips", []),
        }
    }
    detailed_view = {
        "summary": result.get("summary", ""),
        "suspect_profile": result.get("suspect_profile") or "Unknown",
        "clues": result.get("clues", []),
        "artifacts": result.get("artifacts", {}),
        "tool_results": {
            "whois": result.get("whois", {}),
            "dns": result.get("dns", {}),
            "ip_info": result.get("ip_info", {}),
            "url_analysis": result.get("url_analysis", {}),
            "file_metadata": result.get("file_metadata", {})
        }
    }
    return jsonify({
        "status": "success",
        "dashboard": dashboard_view,
        "detailed": detailed_view
    }), 200