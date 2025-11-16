# 🏥 ScanCare Multi-Agent Medical Analysis System

> **"Better than a doctor"** - A sophisticated AI-powered medical report analyzer using Google's ADK multi-agent framework

## 🌟 What Makes ScanCare Special

ScanCare isn't just another AI chatbot. It's a **multi-agent workflow system** where specialized AI agents work together to provide medical-grade analysis that rivals professional consultation.

### The Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                              │
│  (Medical Report, Image, PDF, Text, or Question)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           🤖 AGENT 1: ReportExtractionAgent                 │
│  • Extracts structured data from any format                │
│  • Pattern recognition for medical values                  │
│  • OCR for scanned reports (via Gemini Vision)            │
│  • Output: Structured JSON with all test values           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           📊 AGENT 2: MedicalAnalysisAgent                  │
│  • Compares values against medical ranges                  │
│  • Calculates derived metrics (risk scores, ratios)       │
│  • Identifies abnormalities and concerns                   │
│  • Uses medical knowledge tools internally                 │
│  • Output: Clinical interpretation + risk assessment       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          💬 AGENT 3: ConversationalAgent                    │
│  • Translates medical jargon to patient-friendly language  │
│  • Maintains conversation context                          │
│  • Answers follow-up questions contextually               │
│  • Provides empathetic, supportive guidance                │
│  • Output: Clear, actionable insights                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMPREHENSIVE RESPONSE                     │
│  📋 Test Results Summary                                    │
│  ⚠️  Areas of Concern                                       │
│  ✅ Normal Results                                          │
│  💡 What This Means                                         │
│  🔍 Questions for Your Doctor                              │
│  ⚕️  Medical Disclaimer                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Medical Tools & Functions

Each agent can use specialized medical tools:

### Tool 1: `extract_medical_values()`
- Pattern-based extraction using medical regex
- Identifies: BP, Hemoglobin, Glucose, Cholesterol, HbA1c, WBC, RBC, Platelets, etc.
- Preserves units and context

### Tool 2: `check_normal_ranges()`
- Compares values against medical reference ranges
- Gender-specific ranges where applicable
- Returns: normal/high/low status for each value

### Tool 3: `calculate_health_metrics()`
- Cholesterol/HDL ratio for cardiovascular risk
- Diabetes risk from HbA1c levels
- Derived metrics and risk scores

### Tool 4: `search_medical_knowledge()`
- Medical guideline lookup
- Treatment recommendations
- Evidence-based information retrieval

## 🚀 Getting Started

### Prerequisites
```bash
# Python 3.12+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Get your Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **Add to .env file:**
```bash
GEMINI_API_KEY=your_api_key_here
```

3. **Run the server:**
```bash
python app.py
```

4. **Access ScanCare:**
```
http://localhost:8080
```

## 📡 API Endpoints

### POST `/analyze`
Main multi-agent analysis endpoint

**Input Options:**
```json
// 1. Text report
{
  "report_text": "Hemoglobin: 11.2 g/dL\nGlucose: 126 mg/dL..."
}

// 2. General health question
{
  "query": "What does high cholesterol mean?"
}

// 3. File upload (form-data)
// Key: report_file
// Value: <file> (txt, pdf, docx, jpg, png)
```

**Response:**
```json
{
  "status": "success",
  "analysis_type": "comprehensive_report",
  "workflow_steps": [
    "🔍 Extracting medical data from report...",
    "📊 Analyzing test results and checking ranges...",
    "✅ Analysis complete!"
  ],
  "analysis": "📊 **Test Results Summary**\n...",
  "extracted_data": {
    "numerical_values": {
      "hemoglobin": 11.2,
      "glucose": 126
    },
    "range_analysis": {
      "hemoglobin": {
        "value": 11.2,
        "status": "low",
        "range": "13.5-17.5"
      }
    }
  },
  "agent_system": "multi_agent_workflow"
}
```

### POST `/chat`
Conversational follow-up with context awareness

```json
{
  "message": "What should I do about my low hemoglobin?"
}
```

Response includes context from previous analysis.

### POST `/reset`
Clear conversation history and start fresh

### GET `/health`
System health check and agent status

## 💡 Usage Examples

### Example 1: Analyze a Blood Test Report

```python
import requests

report = """
BLOOD TEST RESULTS
Date: Nov 15, 2025

Hemoglobin: 11.2 g/dL
Glucose: 126 mg/dL
Cholesterol: 245 mg/dL
HDL: 38 mg/dL
Blood Pressure: 145/92 mmHg
HbA1c: 6.8%
"""

response = requests.post(
    "http://localhost:8080/analyze",
    json={"report_text": report}
)

result = response.json()
print(result['analysis'])
```

### Example 2: Upload Image of Report

```python
files = {'report_file': open('medical_report.jpg', 'rb')}
response = requests.post(
    "http://localhost:8080/analyze",
    files=files
)
```

### Example 3: Conversational Q&A

```python
# First analyze report
response1 = requests.post(
    "http://localhost:8080/analyze",
    json={"report_text": report}
)

# Then ask follow-up questions with context
response2 = requests.post(
    "http://localhost:8080/chat",
    json={"message": "Is my diabetes risk high based on these values?"}
)
```

## 🧪 Test the System

See [MULTI_AGENT_TEST.md](MULTI_AGENT_TEST.md) for sample reports and comprehensive testing guide.

## 🎯 Key Features

### 1. **Intelligent Extraction**
- Handles messy reports with OCR
- Multi-format support (text, PDF, images)
- Pattern recognition + AI extraction

### 2. **Clinical-Grade Analysis**
- Medical reference ranges
- Risk stratification
- Abnormality detection
- Derived metric calculations

### 3. **Context-Aware Conversations**
- Maintains analysis context
- Personalized follow-up answers
- Session-based memory
- Natural language understanding

### 4. **Better Than Single-AI Solutions**
- **Traditional AI**: One model does everything (prone to errors)
- **ScanCare**: Specialized agents with specific expertise
  - Extraction agent focuses on data accuracy
  - Analysis agent focuses on medical interpretation
  - Conversational agent focuses on patient communication

### 5. **Transparent Workflow**
- Shows which agents were used
- Logs workflow steps
- Detailed metadata for debugging

## 🏗️ Architecture Deep Dive

### Session Management
```python
# Each user gets their own workflow instance
user_workflows = {}  # session_id -> ScanCareWorkflow

# Maintains context across requests
workflow.current_context = {
    'extracted_data': {...},
    'analysis_summary': "...",
    'timestamp': "2025-11-15T..."
}
```

### Agent Coordination
```python
class ScanCareWorkflow:
    def process_medical_report(self, report_text):
        # Step 1: Extraction
        data = self.extractor.extract(report_text)
        
        # Step 2: Analysis
        analysis = self.analyzer.analyze(data)
        
        # Step 3: Store context for follow-ups
        self.current_context = {
            'extracted_data': data,
            'analysis': analysis
        }
        
        return analysis
```

### Tool Integration
```python
class MedicalAnalysisAgent:
    def __init__(self):
        self.tools = [
            extract_medical_values,
            check_normal_ranges,
            calculate_health_metrics
        ]
    
    def analyze(self, data):
        # Agent can call tools as needed
        ranges = check_normal_ranges(data['values'])
        metrics = calculate_health_metrics(data)
        # Generate comprehensive analysis
```

## 📊 Supported Medical Tests

- **Hematology**: Hemoglobin, WBC, RBC, Platelets
- **Metabolic**: Glucose, HbA1c
- **Lipid Panel**: Total Cholesterol, HDL, LDL, Triglycerides
- **Vital Signs**: Blood Pressure
- **Kidney Function**: Creatinine, BUN (coming soon)
- **Liver Function**: ALT, AST, Bilirubin (coming soon)
- **Thyroid**: TSH, T3, T4 (coming soon)

## 🔐 Security & Privacy

- No data persistence (reports are not stored)
- Temporary files deleted after processing
- Session-based isolation
- HIPAA-conscious design
- API key security via environment variables

## 🚨 Important Disclaimer

**ScanCare is an educational tool designed to help you understand medical reports. It is NOT a substitute for professional medical advice, diagnosis, or treatment.**

Always consult with qualified healthcare professionals for:
- Medical diagnosis
- Treatment decisions
- Medication changes
- Emergency situations

## 🛣️ Roadmap

- [ ] Add more medical test types
- [ ] PDF/DOCX text extraction
- [ ] Trend analysis (compare multiple reports over time)
- [ ] Personalized health recommendations
- [ ] Export reports as PDF
- [ ] Mobile app
- [ ] Voice input support
- [ ] Integration with EHR systems

## 🤝 Contributing

This is an open-source project. Contributions welcome!

## 📄 License

MIT License - Feel free to use and modify

## 🙏 Acknowledgments

- Built with Google Gemini 2.0 Flash
- Powered by Google ADK (Agent Development Kit)
- Medical reference ranges from clinical guidelines

---

**Built with ❤️ for better healthcare accessibility**

*ScanCare - Understanding your health, one report at a time.*
