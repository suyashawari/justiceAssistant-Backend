

# from app.utils.openrouter_agent import run_analysis_agent

# def analyze_report_task(report_id):
#     try:
#         from app.models import create_app, db
#         from app.models.models import Report
#     except Exception as e:
#         print(f"Import error inside RQ task: {e}")
#         return
    
#     app = create_app()
#     with app.app_context():
#         report = None
#         try:
#             report = Report.query.get(report_id)
#             if not report:
#                 print(f"Report ID {report_id} not found.")
#                 return

#             print(f"Handing off report {report_id} to the AI agent...")
            
#             # UPDATED: Pass the report's evidence_file path to the agent
#             analysis_result = run_analysis_agent(
#                 text_to_analyze=report.description,
#                 report_id=report.id,
#                 file_path=report.evidence_file  # Pass the file path here
#             )

#             # Handle potential errors from the agent
#             if "error" in analysis_result:
#                 print(f"AI agent failed for report {report_id}: {analysis_result['error']}")
#                 report.status = 'failed'
#                 # Optionally save the error details for debugging
#                 report.set_json_field("forensic_details", analysis_result)
#                 db.session.add(report)
#                 db.session.commit()
#                 return

#             executive_summary = analysis_result.get("executive_summary", {})
#             dashboard_summary = {
#                 "summary": executive_summary.get("summary", "Analysis complete."),
#                 "suspect_profile": executive_summary.get("suspect_profile", "Unknown")
#             }
            
#             report.set_json_field("forensic_summary", dashboard_summary)
#             report.set_json_field("forensic_details", analysis_result)
#             report.status = "analyzed"
            
#             db.session.add(report)
#             db.session.commit()
            
#             print(f"AI agent finished for report {report_id}. Detailed results saved.")

#         except Exception as e:
#             if db.session.is_active:
#                 db.session.rollback()
#             print(f"Exception during AI agent task for report {report_id}: {e}")
#             import traceback
#             traceback.print_exc()
#             if report:
#                 report.status = 'failed'
#                 db.session.add(report)
#                 db.session.commit()


# app/tasks.py
# app/tasks.py

from app.utils.openrouter_agent import run_analysis_agent
from datetime import datetime
import json

def analyze_report_task(report_id):
    try:
        from app.models import create_app, db
        from app.models.models import Report
    except Exception as e:
        print(f"Import error inside RQ task: {e}")
        return

    app = create_app()
    with app.app_context():
        report = None
        try:
            report = Report.query.get(report_id)
            if not report:
                print(f"Report ID {report_id} not found.")
                return

            print(f"Handing off report {report_id} to the AI agent...")
            report.status = 'analyzing'
            db.session.commit()

            raw_findings = run_analysis_agent(
                text_to_analyze=report.description,
                report_id=report.id,
                file_path=report.evidence_file
            )

            if "error" in raw_findings:
                print(f"AI agent failed for report {report_id}: {raw_findings['error']}")
                report.status = 'failed'
                report.set_json_field("forensic_details", raw_findings)
                db.session.commit()
                return

            # --- NEW AND CORRECTED LOGIC FOR FINDING ARTIFACTS ---
            # We will now search the tool_results list to find the artifacts.
            indicators_of_compromise = {}
            for tool_run in raw_findings.get("tool_results", []):
                if tool_run.get("tool") == "extract_artifacts":
                    # Found it! Get the output from this tool run.
                    indicators_of_compromise = tool_run.get("output", {})
                    break # Stop searching once we've found it.
            # --- END OF NEW LOGIC ---

            incident_type = report.complaint_category or "Unknown"
            suspect_profile = "A suspect involved in online malicious activities."
            if "crypto" in incident_type.lower():
                suspect_profile = "Fraudster operating a fake crypto investment scheme."
            elif "phishing" in incident_type.lower() or "email" in incident_type.lower():
                suspect_profile = "Scammer using deceptive emails/websites to steal credentials."

            executive_summary = {
                "summary": raw_findings.get("final_summary_text", "Analysis complete.").strip(),
                "suspect_profile": suspect_profile,
                "incident_type": incident_type
            }

            analysis_details = {
                "executive_summary": executive_summary,
                # Use the indicators we just found
                "indicators_of_compromise": indicators_of_compromise,
                "tool_investigation_results": raw_findings.get("tool_results", []),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "report_id": report_id
            }
            
            dashboard_summary = {
                "summary": executive_summary["summary"],
                "suspect_profile": executive_summary["suspect_profile"]
            }

            report.set_json_field("forensic_summary", dashboard_summary)
            report.set_json_field("forensic_details", analysis_details)
            report.status = "analyzed"
            db.session.commit()

            print(f"AI agent finished for report {report_id}. Detailed results structured and saved successfully.")

        except Exception as e:
            if db.session.is_active:
                db.session.rollback()
            print(f"Exception during AI agent task for report {report_id}: {e}")
            import traceback
            traceback.print_exc()
            if report:
                report.status = 'failed'
                db.session.commit()