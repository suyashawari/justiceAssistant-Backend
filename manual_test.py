# manual_test.py

import os
import json
from dotenv import load_dotenv
from app.models import create_app
from app.utils.openrouter_agent import run_analysis_agent

load_dotenv()

complex_test_text = """
I was contacted on WhatsApp by a person who slowly gained my trust and then 
introduced me to a crypto trading platform at https://www.apex-quant-trade.com. 
Their 'investment advisor' using the email 'linda.chen@apex-advisors.net' guided me. 
I transferred a total of 1.5 ETH to their wallet address: 0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B. 
Now, the website is down and they are not responding.
"""

app = create_app()

with app.app_context():
    print("="*60)
    print("      MANUAL TEST SCRIPT FOR ROBUST HYBRID AI WORKFLOW")
    print("="*60)
    
    print("\n[INPUT] Using the following text for analysis:")
    print("---------------------------------------------")
    print(complex_test_text.strip())
    print("---------------------------------------------")

    print("\n[STEP 1] Calling the main agent (`run_analysis_agent`)...")
    print("         This will test the hybrid workflow:")
    print("         1. Python code will force the first tool call (`extract_artifacts`).")
    print("         2. The AI will be asked to investigate the results.")
    
    analysis_result = run_analysis_agent(text_to_analyze=complex_test_text, report_id=999)

    print("\n" + "="*60)
    print("      AGENT WORKFLOW COMPLETE")
    print("="*60)
    
    print("\n[RAW FINDINGS] The raw dictionary produced by the agent is:")
    print("----------------------------------------------------------")
    print(json.dumps(analysis_result, indent=2))
    print("----------------------------------------------------------")

    print("\n[VERIFICATION]")
    print("Check the raw findings. It should contain 'initial_artifacts' and 'tool_results'.")
    print("This proves the hybrid workflow is functioning correctly before the final report is built.")
    print("\n✅ Manual test script finished.")
    print("="*60 )