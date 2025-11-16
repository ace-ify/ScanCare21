# config.py
# Configuration for ScanCare medical report analysis

# Medical AI configuration
MEDICAL_DISCLAIMER = """
⚕️ IMPORTANT MEDICAL DISCLAIMER:
This analysis is provided by an AI system and should not replace professional medical advice, 
diagnosis, or treatment. Always seek the advice of your physician or other qualified health 
provider with any questions you may have regarding a medical condition.
"""

# Supported medical report formats
SUPPORTED_FORMATS = {
    'text': ['.txt'],
    'documents': ['.pdf', '.docx'],
    'images': ['.jpg', '.jpeg', '.png']
# Load Gemini API key from .env
import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
}

# AI Model configuration
AI_MODEL = 'gemini-2.0-flash-exp'
AI_TEMPERATURE = 0.7  # Balance between creativity and accuracy

# Medical analysis prompts
MEDICAL_ANALYSIS_PROMPT_TEMPLATE = """You are ScanCare, a helpful medical AI assistant that analyzes medical reports and provides insights.

When analyzing medical reports:
1. Extract and summarize key findings
2. Explain medical terminology in simple terms
3. Highlight important values and their normal ranges
4. Identify potential concerns or abnormalities
5. Suggest relevant follow-up questions for healthcare providers

IMPORTANT: Always include a disclaimer that this is AI analysis and users should consult with healthcare professionals for medical advice.

Be empathetic, clear, and focus on helping patients understand their reports better."""

HEALTH_QUERY_PROMPT_TEMPLATE = """You are ScanCare, a helpful medical AI assistant that answers health-related questions.

Provide accurate, evidence-based information while:
1. Being clear and easy to understand
2. Explaining medical concepts in layman's terms
3. Highlighting when professional medical consultation is needed
4. Being empathetic and supportive

IMPORTANT: Always remind users that AI advice should not replace professional medical consultation."""
