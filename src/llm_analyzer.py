import os
import json
from groq import Groq
from pydantic import BaseModel, Field
from typing import List

class RenewalBriefSchema(BaseModel):
    final_integrated_risk_tier: str = Field(description="Must be exactly 'High', 'Medium', or 'Low'")
    root_cause_analysis: str = Field(description="Concise plain-English summary of driving risk vectors")
    non_obvious_insight: str = Field(description="Hidden nuance matching logs to product updates or soft sentiment cues")
    recommended_actions: List[str] = Field(description="2-3 explicit prioritized playbook action items")

class LLMRenewalAnalyzer:
    def __init__(self, api_key: str = None):
        # Initialize the official Groq client wrapper
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        # Using Llama 3 70B - highly capable of complex logical reasoning
        self.model = "openai/gpt-oss-120b"

    def extract_relevant_csm_notes(self, account_name: str, raw_csm_text: str) -> str:
        lines = [line for line in raw_csm_text.split('\n') if account_name.lower() in line.lower()]
        return "\n".join(lines) if lines else "No specific CSM entries noted."

    def generate_account_brief(self, account_row: dict, csm_context: str, changelog: str) -> dict:
        system_prompt = (
            "You are an elite Director of BizOps at Contentstack. Synthesize structured quantitative telemetry "
            "and unstructured notes into a structured JSON brief matching the requested schema exactly. "
            "Return ONLY a valid JSON object with keys: 'final_integrated_risk_tier', 'root_cause_analysis', 'non_obvious_insight', and 'recommended_actions'."
        )
        user_content = (
            f"Analyze upcoming renewal state:\n"
            f"Name: {account_row['account_name']}\n"
            f"ARR: ${account_row['arr']}\n"
            f"Usage Trend: {account_row['usage_mom_change']:.1%}\n"
            f"Tickets: {account_row['high_sev_tickets']}\n"
            f"NPS: {account_row['nps_score']}\n"
            f"Logs:\n{csm_context}\n"
            f"Changelog:\n{changelog}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            raw_text = response.choices[0].message.content
            parsed_json = json.loads(raw_text)
            
            # 🌟 HELPER RULE: Coerce keys to lowercase snake_case to match app.py expectations perfectly
            clean_json = {}
            for k, v in parsed_json.items():
                clean_key = k.lower().strip().replace(" ", "_")
                clean_json[clean_key] = v
                
            return clean_json
            
        except Exception as e:
            return {
                "final_integrated_risk_tier": account_row['quantitative_risk_tier'],
                "root_cause_analysis": f"Live Synthesis Error: {str(e)}",
                "non_obvious_insight": "Telemetry notes indicate heavy ticket activity over past 30 days.",
                "recommended_actions": [
                    "Initiate direct stakeholder touchpoint sync.",
                    "Review outstanding technical engineering blockers."
                ]
            }