"""
ScanCare Multi-Agent System
A sophisticated medical analysis workflow powered by Google Generative AI
"""

import os
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai import types
import json
import re
from datetime import datetime

# ==============================================
# MEDICAL TOOLS - Functions agents can call
# ==============================================

def extract_medical_values(report_text: str) -> str:
    """
    Extract numerical values and medical terms from reports.
    Returns JSON string of all medical values found.
    
    Args:
        report_text: The medical report text to analyze
        
    Returns:
        JSON string with extracted medical values
    """
    # Common patterns for medical values
    patterns = {
        'blood_pressure': r'(?:BP|Blood Pressure)[:\s]*(\d{2,3})/(\d{2,3})',
        'hemoglobin': r'(?:Hb|Hemoglobin)[:\s]*(\d+\.?\d*)\s*(?:g/dL|g/dl)',
        'glucose': r'(?:Glucose|Blood Sugar|FBS)[:\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)',
        'cholesterol': r'(?:Cholesterol|Total Cholesterol)[:\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)',
        'hdl': r'(?:HDL)[:\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)',
        'ldl': r'(?:LDL)[:\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)',
        'triglycerides': r'(?:Triglycerides)[:\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)',
        'wbc': r'(?:WBC|White Blood Cell)[:\s]*(\d+\.?\d*)',
        'rbc': r'(?:RBC|Red Blood Cell)[:\s]*(\d+\.?\d*)',
        'platelets': r'(?:Platelet)[:\s]*(\d+\.?\d*)',
        'hba1c': r'(?:HbA1c|A1C)[:\s]*(\d+\.?\d*)\s*%?',
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, report_text, re.IGNORECASE)
        if match:
            if key == 'blood_pressure':
                extracted[key] = f"{match.group(1)}/{match.group(2)}"
            else:
                extracted[key] = float(match.group(1))
    
    return json.dumps(extracted, indent=2)


def check_normal_ranges(values_json: str) -> str:
    """
    Compare extracted values against normal medical ranges.
    Returns JSON string with status (normal/high/low) for each value.
    
    Args:
        values_json: JSON string of medical values from extract_medical_values
        
    Returns:
        JSON string with range analysis for each value
    """
    try:
        values = json.loads(values_json)
    except:
        return json.dumps({"error": "Invalid JSON input"})
    
    normal_ranges = {
        'hemoglobin': {'male': (13.5, 17.5), 'female': (12.0, 15.5), 'unit': 'g/dL'},
        'glucose': {'fasting': (70, 100), 'random': (70, 140), 'unit': 'mg/dL'},
        'cholesterol': {'normal': (0, 200), 'borderline': (200, 240), 'unit': 'mg/dL'},
        'hdl': {'male': (40, float('inf')), 'female': (50, float('inf')), 'unit': 'mg/dL'},
        'ldl': {'optimal': (0, 100), 'near_optimal': (100, 130), 'unit': 'mg/dL'},
        'triglycerides': {'normal': (0, 150), 'borderline': (150, 200), 'unit': 'mg/dL'},
        'wbc': {'normal': (4.0, 11.0), 'unit': 'thousands/μL'},
        'rbc': {'male': (4.5, 5.5), 'female': (4.0, 5.0), 'unit': 'millions/μL'},
        'platelets': {'normal': (150, 400), 'unit': 'thousands/μL'},
        'hba1c': {'normal': (0, 5.7), 'prediabetes': (5.7, 6.5), 'unit': '%'},
        'blood_pressure': {'normal': (90, 120, 60, 80), 'unit': 'mmHg'}
    }
    
    results = {}
    for key, value in values.items():
        if key not in normal_ranges:
            continue
            
        range_data = normal_ranges[key]
        
        if key == 'blood_pressure':
            sys, dia = map(int, value.split('/'))
            sys_status = 'normal' if range_data['normal'][0] <= sys <= range_data['normal'][1] else 'high' if sys > range_data['normal'][1] else 'low'
            dia_status = 'normal' if range_data['normal'][2] <= dia <= range_data['normal'][3] else 'high' if dia > range_data['normal'][3] else 'low'
            status = 'normal' if sys_status == 'normal' and dia_status == 'normal' else 'abnormal'
            results[key] = {
                'value': value,
                'status': status,
                'systolic_status': sys_status,
                'diastolic_status': dia_status,
                'unit': range_data['unit']
            }
        else:
            # Use first available range
            range_key = list(range_data.keys())[0] if 'normal' not in range_data else 'normal'
            if range_key != 'unit':
                min_val, max_val = range_data[range_key]
                status = 'normal' if min_val <= value <= max_val else 'high' if value > max_val else 'low'
                results[key] = {
                    'value': value,
                    'status': status,
                    'range': f"{min_val}-{max_val}",
                    'unit': range_data.get('unit', '')
                }
    
    return json.dumps(results, indent=2)


def calculate_health_metrics(values_json: str) -> str:
    """
    Calculate derived health metrics like BMI, cardiovascular risk, etc.
    
    Args:
        values_json: JSON string of medical values
        
    Returns:
        JSON string with calculated health metrics and risk assessments
    """
    try:
        data = json.loads(values_json)
    except:
        return json.dumps({"error": "Invalid JSON input"})
    
    metrics = {}
    
    # Cardiovascular risk based on cholesterol ratios
    if 'cholesterol' in data and 'hdl' in data:
        ratio = data['cholesterol'] / data['hdl']
        risk = 'low' if ratio < 3.5 else 'moderate' if ratio < 5.0 else 'high'
        metrics['cholesterol_hdl_ratio'] = {
            'value': round(ratio, 2),
            'risk_level': risk,
            'description': 'Total Cholesterol to HDL ratio - indicator of cardiovascular risk'
        }
    
    # Diabetes risk from HbA1c
    if 'hba1c' in data:
        hba1c = data['hba1c']
        if hba1c < 5.7:
            risk = 'normal'
            message = 'No diabetes detected'
        elif hba1c < 6.5:
            risk = 'prediabetes'
            message = 'Prediabetes - lifestyle changes recommended'
        else:
            risk = 'diabetes'
            message = 'Diabetes range - consult doctor immediately'
        
        metrics['diabetes_risk'] = {
            'value': hba1c,
            'category': risk,
            'message': message
        }
    
    # Anemia assessment
    if 'hemoglobin' in data:
        hb = data['hemoglobin']
        if hb < 12.0:
            severity = 'severe' if hb < 8.0 else 'moderate' if hb < 10.0 else 'mild'
            metrics['anemia_assessment'] = {
                'detected': True,
                'severity': severity,
                'hemoglobin': hb,
                'recommendation': 'Consult doctor for iron supplementation or further testing'
            }
        else:
            metrics['anemia_assessment'] = {
                'detected': False,
                'hemoglobin': hb
            }
    
    # Blood pressure category
    if 'blood_pressure' in data:
        sys, dia = map(int, data['blood_pressure'].split('/'))
        if sys < 120 and dia < 80:
            category = 'Normal'
        elif sys < 130 and dia < 80:
            category = 'Elevated'
        elif sys < 140 or dia < 90:
            category = 'Stage 1 Hypertension'
        else:
            category = 'Stage 2 Hypertension'
        
        metrics['blood_pressure_category'] = {
            'systolic': sys,
            'diastolic': dia,
            'category': category,
            'action_needed': category != 'Normal'
        }
    
    return json.dumps(metrics, indent=2)


def search_medical_guidelines(condition: str) -> str:
    """
    Search for medical guidelines and recommendations for a specific condition.
    
    Args:
        condition: Medical condition or test name to search for
        
    Returns:
        Medical guidelines and recommendations as a string
    """
    # Medical knowledge base
    guidelines = {
        'high_cholesterol': """
High Cholesterol Management Guidelines:
- Dietary Changes: Reduce saturated fats, increase fiber, eat more fruits/vegetables
- Exercise: At least 150 minutes of moderate aerobic activity per week
- Weight Management: Lose 5-10% of body weight if overweight
- Medication: Statins may be prescribed if lifestyle changes insufficient
- Follow-up: Retest lipid panel every 3-6 months
        """,
        'high_blood_pressure': """
Hypertension Management Guidelines:
- Dietary: DASH diet - reduce sodium to <2,300mg/day, ideally <1,500mg/day
- Exercise: Regular physical activity 30 minutes most days
- Weight: Lose weight if BMI >25
- Limit Alcohol: Max 2 drinks/day for men, 1 for women
- Stress Management: Practice relaxation techniques
- Medication: May require antihypertensive drugs
- Monitoring: Home blood pressure monitoring recommended
        """,
        'diabetes': """
Diabetes Management Guidelines:
- Blood Sugar Monitoring: Check regularly as prescribed
- Diet: Carbohydrate counting, consistent meal times, fiber-rich foods
- Exercise: 150 minutes/week of moderate activity
- Medication: Metformin often first-line, insulin if needed
- HbA1c Goal: Generally <7% (individualized)
- Regular Screening: Eyes, kidneys, feet, cardiovascular risk
- Education: Diabetes self-management education programs
        """,
        'prediabetes': """
Prediabetes Prevention Guidelines:
- Weight Loss: 7-10% of body weight can reduce diabetes risk by 58%
- Exercise: 150 minutes/week moderate activity (brisk walking)
- Diet: Mediterranean or DASH diet, reduce processed foods
- Sleep: 7-9 hours per night
- Stress: Manage chronic stress
- Monitoring: Retest HbA1c annually
- Consider: Metformin if high risk
        """,
        'anemia': """
Anemia Management Guidelines:
- Iron Deficiency: Iron supplementation, iron-rich foods (red meat, spinach, beans)
- Vitamin B12: Supplements if deficient, dietary sources (meat, fish, dairy)
- Folate: Leafy greens, fortified cereals
- Avoid: Tea/coffee with meals (reduces iron absorption)
- Investigation: May need endoscopy if cause unclear
- Follow-up: Recheck hemoglobin in 4-6 weeks
        """
    }
    
    condition_lower = condition.lower().replace(' ', '_')
    
    for key, guideline in guidelines.items():
        if key in condition_lower or condition_lower in key:
            return guideline
    
    return f"General recommendation for {condition}: Consult with a healthcare provider for personalized medical advice and treatment plan."


# ==============================================
# GOOGLE GENERATIVE AI MODELS - Initialized lazily
# ==============================================

_medical_analyzer_model = None
_health_chat_model = None


def _init_agents(api_key: str):
    """Initialize Gemini models with function calling capabilities."""
    global _medical_analyzer_model, _health_chat_model
    
    if _medical_analyzer_model is None:
        genai.configure(api_key=api_key)
        
        # Medical Analyzer with tools
        _medical_analyzer_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[extract_medical_values, check_normal_ranges, calculate_health_metrics, search_medical_guidelines],
            system_instruction="""You are Dr. ScanCare, an expert medical AI assistant specializing in analyzing medical reports.

Your Role:
- Analyze medical test results with clinical precision
- Extract key values from reports and check them against normal ranges
- Calculate health metrics and risk assessments
- Explain findings in patient-friendly language
- Provide evidence-based recommendations

When analyzing reports:
1. Use extract_medical_values() to find all test values
2. Use check_normal_ranges() to assess each value
3. Use calculate_health_metrics() for risk calculations
4. Use search_medical_guidelines() for condition-specific recommendations

Always structure your response as:
📊 **Test Results Summary**
⚠️ **Areas of Concern** (if any)
✅ **Normal Results**
💡 **What This Means** (explain in simple terms)
🔍 **Questions for Your Doctor**
📋 **Recommended Actions**
⚕️ **Important Disclaimer**

Be empathetic, clear, and emphasize when professional consultation is needed."""
        )
        
        # Health Chat Assistant
        _health_chat_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[search_medical_guidelines],
            system_instruction="""You are ScanCare, a friendly and knowledgeable medical AI assistant for general health questions.

Your Personality:
- Warm, empathetic, and patient
- Clear communicator who avoids medical jargon
- Encouraging and supportive
- Evidence-based and accurate

Your Capabilities:
- Answer health questions with reliable information
- Explain medical concepts in simple terms
- Provide lifestyle and wellness guidance
- Use search_medical_guidelines() for condition-specific information

Important Guidelines:
- Always remind users that AI advice doesn't replace professional medical care
- Encourage users to consult healthcare providers for diagnosis and treatment
- Be honest about limitations and uncertainties
- Provide actionable, practical advice when appropriate

Maintain a supportive, educational tone."""
        )
    
    return _medical_analyzer_model, _health_chat_model


# ==============================================
# WORKFLOW ORCHESTRATOR
# ==============================================

class ScanCareWorkflow:
    """
    Main workflow orchestrator using Google Generative AI with function calling.
    Coordinates medical analysis and conversational interactions.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Initialize Gemini models with function calling
        self.medical_analyzer_model, self.health_chat_model = _init_agents(api_key)
        
        # Create chat sessions for stateful conversations
        self.analyzer_chat = self.medical_analyzer_model.start_chat(enable_automatic_function_calling=True)
        self.health_chat = self.health_chat_model.start_chat(enable_automatic_function_calling=True)
        
        # Context for maintaining conversation state
        self.current_context = {}
        self.conversation_history = []
    
    def process_medical_report(self, report_text: str, user_query: str = "") -> Dict[str, Any]:
        """
        Complete workflow for processing a medical report using Gemini with function calling.
        
        Steps:
        1. Use medical_analyzer_model to analyze the report
        2. Model automatically calls tools as needed with automatic function calling
        3. Store context for follow-up questions
        """
        
        workflow_log = []
        workflow_log.append("🔍 Analyzing medical report with AI agent...")
        
        # Create the analysis prompt
        analysis_prompt = f"""Analyze this medical report:

{report_text}

Please:
1. Extract all medical values using the extract_medical_values tool
2. Check each value against normal ranges using check_normal_ranges
3. Calculate health metrics using calculate_health_metrics
4. Search for relevant guidelines using search_medical_guidelines if needed
5. Provide a comprehensive patient-friendly analysis

{user_query if user_query else ""}"""
        
        # Let Gemini handle everything with automatic function calling
        response = self.analyzer_chat.send_message(analysis_prompt)
        
        workflow_log.append("📊 Analysis complete with tool calls!")
        workflow_log.append("✅ Results formatted for patient understanding")
        
        # Extract data for context (simplified)
        try:
            # Try to extract values directly for context
            extracted_json = extract_medical_values(report_text)
            extracted_data = json.loads(extracted_json)
        except:
            extracted_data = {}
        
        # Store context for follow-ups
        self.current_context = {
            'report_text': report_text[:500],
            'extracted_values': extracted_data,
            'analysis_summary': response.text[:500],
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'type': 'report_analysis',
            'analysis': response.text,
            'extracted_data': extracted_data,
            'workflow_steps': workflow_log
        }
    
    def handle_conversation(self, user_message: str, is_report: bool = False) -> Dict[str, Any]:
        """
        Handle any user interaction - report analysis or general questions.
        Routes to appropriate Gemini model with function calling.
        """
        
        if is_report:
            # This is a medical report to analyze - use analyzer model
            result = self.process_medical_report(user_message, "")
            return result
        else:
            # Regular health question - use chat model
            # Add context if available
            context_text = ""
            if self.current_context:
                context_text = f"\n\nContext from previous analysis:\n{json.dumps(self.current_context, indent=2)}\n\n"
            
            prompt = context_text + user_message
            response = self.health_chat.send_message(prompt)
            
            # Update conversation history
            self.conversation_history.append({
                'user': user_message,
                'assistant': response.text,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'type': 'conversation',
                'response': response.text
            }
    
    def ask_followup(self, question: str) -> str:
        """
        Handle follow-up questions with context from previous analysis.
        Uses health chat model with context awareness.
        """
        # Build context-aware prompt
        context_text = ""
        if self.current_context:
            context_text = f"""Previous Analysis Context:
{json.dumps(self.current_context, indent=2)}

Recent Conversation:
{json.dumps(self.conversation_history[-3:], indent=2) if self.conversation_history else 'No previous conversation'}

"""
        
        prompt = f"{context_text}User Question: {question}"
        
        # Use chat model for follow-ups
        response = self.health_chat.send_message(prompt)
        
        # Update history
        self.conversation_history.append({
            'user': question,
            'assistant': response.text,
            'timestamp': datetime.now().isoformat()
        })
        
        return response.text
    
    def reset(self):
        """Reset workflow state and conversation history"""
        self.current_context = {}
        self.conversation_history = []
        # Restart chat sessions
        self.analyzer_chat = self.medical_analyzer_model.start_chat(enable_automatic_function_calling=True)
        self.health_chat = self.health_chat_model.start_chat(enable_automatic_function_calling=True)
