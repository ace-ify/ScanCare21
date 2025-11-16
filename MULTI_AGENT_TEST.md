# ScanCare Multi-Agent System Test

## Sample Medical Report for Testing

This is a sample blood test report you can use to test the multi-agent system.

```
COMPLETE BLOOD COUNT (CBC) REPORT
Patient: John Doe
Date: November 15, 2025

TEST RESULTS:
-------------
Hemoglobin: 11.2 g/dL (Normal Range: 13.5-17.5 g/dL)
White Blood Cell Count (WBC): 12.5 thousands/μL (Normal: 4.0-11.0)
Red Blood Cell Count (RBC): 4.8 millions/μL (Normal: 4.5-5.5)
Platelets: 185 thousands/μL (Normal: 150-400)
Glucose (Fasting): 126 mg/dL (Normal: 70-100)
Total Cholesterol: 245 mg/dL (Desirable: <200)
HDL Cholesterol: 38 mg/dL (Optimal: >40)
LDL Cholesterol: 165 mg/dL (Optimal: <100)
Triglycerides: 210 mg/dL (Normal: <150)
Blood Pressure: 145/92 mmHg
HbA1c: 6.8% (Normal: <5.7%)

NOTES:
- Patient reports fatigue and occasional dizziness
- Family history of diabetes and heart disease
- Currently not on any medication
```

## Testing the Multi-Agent System

### 1. Test Report Analysis (via API)

```bash
# Using PowerShell
$report = Get-Content "sample_report.txt" -Raw
$body = @{ report_text = $report } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/analyze" -Method POST -Body $body -ContentType "application/json"
```

### 2. Test Conversational Follow-up

```bash
# Ask a follow-up question
$body = @{ message = "What does my low hemoglobin mean?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/chat" -Method POST -Body $body -ContentType "application/json"
```

### 3. Test File Upload

```bash
# Create a text file with the report
$report | Out-File -FilePath "test_report.txt" -Encoding utf8

# Upload it
$uri = "http://localhost:8080/analyze"
$filePath = "test_report.txt"
curl -X POST $uri -F "report_file=@$filePath"
```

## What the Multi-Agent System Does

### Agent 1: ReportExtractionAgent
- Extracts structured data from the report
- Identifies: Hemoglobin, WBC, RBC, Platelets, Glucose, Cholesterol, BP, HbA1c
- Preserves units and values

### Agent 2: MedicalAnalysisAgent
- Compares values against normal ranges
- Calculates health metrics (cholesterol ratio, diabetes risk)
- Identifies abnormalities:
  - ⚠️ Low Hemoglobin (anemia)
  - ⚠️ High WBC (possible infection)
  - ⚠️ High Glucose (prediabetes/diabetes)
  - ⚠️ High Cholesterol & Low HDL
  - ⚠️ High Blood Pressure
  - ⚠️ High HbA1c (diabetes indicator)

### Agent 3: ConversationalAgent
- Provides patient-friendly explanations
- Answers follow-up questions with context
- Maintains conversation history

## Expected Multi-Agent Workflow

```
User Input → ReportExtractionAgent
                    ↓
          [Extracts Values & Structure]
                    ↓
           MedicalAnalysisAgent
                    ↓
    [Checks Ranges, Calculates Metrics]
                    ↓
          ConversationalAgent
                    ↓
       [Generates Patient-Friendly Response]
                    ↓
              User Output
```

## Key Features

1. **Automatic Value Extraction**: Uses regex patterns + AI to find all medical values
2. **Range Checking**: Compares against medical reference ranges
3. **Health Calculations**: Computes risk scores and ratios
4. **Context Awareness**: Remembers previous analysis for follow-ups
5. **Session Management**: Each user gets their own workflow instance
6. **Comprehensive Logging**: Tracks workflow steps and agent usage

## Advanced Testing

### Test with a health question (no report)
```json
POST /analyze
{
  "query": "What are the symptoms of high cholesterol?"
}
```

### Test with an image
Upload a screenshot of a medical report (jpg/png) - the vision agent will extract text first, then analyze.

### Test conversation context
```json
POST /analyze
{ "report_text": "<your report>" }

POST /chat
{ "message": "Should I be worried about my glucose levels?" }

POST /chat
{ "message": "What foods should I avoid?" }
```

The conversational agent will use context from the analyzed report to provide personalized answers.
