from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import base64
from werkzeug.utils import secure_filename

# Load environment variables from .env file
load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Serve assets from templates/public at /public and keep templates working
app = Flask(
    __name__,
    static_folder=os.path.join('templates', 'public'),
    static_url_path='/public'
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scancare.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_event(event_type: str,
              status: str | None = None,
              query: str | None = None,
              response: str | None = None,
              metadata: dict | None = None):
    """Emit a structured JSON event to the log."""
    evt = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "status": status,
        "query": query[:200] if query else None,
        "response_preview": (response[:200] + ("…" if response and len(response) > 200 else "")) if response else None,
        "metadata": metadata or {},
    }
    try:
        logger.info("EVENT_JSON " + json.dumps(evt, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Failed to log structured event: {e}")


@app.route('/')
def home():
    """Render the ScanCare main page."""
    return render_template('test.html')


@app.route('/public/<path:filename>')
def public_assets(filename):
    """Serve assets from templates/public to use as a lightweight public folder."""
    assets_dir = os.path.join(app.root_path, 'templates', 'public')
    return send_from_directory(assets_dir, filename)


@app.route('/analyze', methods=['POST'])
def analyze_report():
    """Analyze medical reports using AI.
    
    Accepts:
    - JSON with 'report_text' field
    - File upload with 'report_file' field
    - JSON with 'query' field for general health questions
    """
    try:
        report_text = None
        analysis_type = "general"
        
        # Check if this is a file upload
        if 'report_file' in request.files:
            file = request.files['report_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract text based on file type
                if filename.lower().endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report_text = f.read()
                    analysis_type = "text_report"
                elif filename.lower().endswith(('.pdf', '.docx')):
                    # For now, inform user about PDF/DOCX support
                    report_text = f"[Uploaded file: {filename}]\n\nNote: PDF and DOCX parsing requires additional libraries. Please paste the text content or use a .txt file."
                    analysis_type = "file_upload"
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Image upload - use Gemini's vision capabilities
                    with open(filepath, 'rb') as img_file:
                        image_data = img_file.read()
                    
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    
                    # Create prompt for medical report analysis
                    prompt = """You are a medical AI assistant analyzing a medical report image. 
                    Please provide:
                    1. Key findings from the report
                    2. Important medical values and their interpretations
                    3. Potential areas of concern (if any)
                    4. Suggestions for follow-up or questions to ask a doctor
                    
                    Be professional, clear, and emphasize that this is an AI analysis and should not replace professional medical advice."""
                    
                    response = model.generate_content([
                        prompt,
                        {"mime_type": f"image/{filename.split('.')[-1]}", "data": image_data}
                    ])
                    
                    ai_analysis = response.text
                    
                    log_event(
                        event_type="ANALYSIS",
                        status="success",
                        query=f"Image report analysis: {filename}",
                        response=ai_analysis,
                        metadata={"type": "image_report", "filename": filename}
                    )
                    
                    return jsonify({
                        "status": "success",
                        "report_type": "image",
                        "filename": filename,
                        "analysis": ai_analysis,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                
                # Clean up uploaded file
                try:
                    os.remove(filepath)
                except:
                    pass
            else:
                return jsonify({"error": "Invalid file type. Allowed types: txt, pdf, docx, png, jpg, jpeg"}), 400
        
        # Check if this is JSON input
        elif request.json:
            data = request.json
            if 'report_text' in data:
                report_text = data['report_text']
                analysis_type = "text_report"
            elif 'query' in data:
                report_text = data['query']
                analysis_type = "health_query"
        
        if not report_text:
            return jsonify({"error": "Please provide 'report_text', 'query', or upload a 'report_file'."}), 400
        
        logger.info(f"Received {analysis_type} analysis request")
        
        # Generate AI analysis using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Create appropriate prompt based on analysis type
        if analysis_type == "text_report":
            system_prompt = """You are ScanCare, a helpful medical AI assistant that analyzes medical reports and provides insights.
            
When analyzing medical reports:
1. Extract and summarize key findings
2. Explain medical terminology in simple terms
3. Highlight important values and their normal ranges
4. Identify potential concerns or abnormalities
5. Suggest relevant follow-up questions for healthcare providers

IMPORTANT: Always include a disclaimer that this is AI analysis and users should consult with healthcare professionals for medical advice.

Be empathetic, clear, and focus on helping patients understand their reports better."""
            
            prompt = f"{system_prompt}\n\nMedical Report:\n{report_text}\n\nProvide a comprehensive analysis:"
        
        elif analysis_type == "health_query":
            system_prompt = """You are ScanCare, a helpful medical AI assistant that answers health-related questions.

Provide accurate, evidence-based information while:
1. Being clear and easy to understand
2. Explaining medical concepts in layman's terms
3. Highlighting when professional medical consultation is needed
4. Being empathetic and supportive

IMPORTANT: Always remind users that AI advice should not replace professional medical consultation."""
            
            prompt = f"{system_prompt}\n\nUser Question: {report_text}\n\nProvide a helpful response:"
        
        else:
            prompt = f"Please analyze this medical content and provide helpful insights:\n\n{report_text}"
        
        response = model.generate_content(prompt)
        ai_analysis = response.text
        
        log_event(
            event_type="ANALYSIS",
            status="success",
            query=report_text,
            response=ai_analysis,
            metadata={"type": analysis_type}
        )
        
        return jsonify({
            "status": "success",
            "report_type": analysis_type,
            "original_text": report_text,
            "analysis": ai_analysis,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        logger.exception(f"Unhandled error in /analyze: {e}")
        log_event(
            event_type="ERROR",
            status="error",
            query=report_text if 'report_text' in locals() else None,
            metadata={"error": str(e)}
        )
        return jsonify({
            "status": "error",
            "error": "Internal error while processing request.",
            "message": str(e)
        }), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Return recent structured events parsed from scancare.log.

    Query params:
      - limit: number of recent lines to scan from the end of the file (default 500)
    """
    log_path = os.path.join(os.getcwd(), "scancare.log")
    limit = request.args.get("limit", default=500, type=int)
    events = []
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Look back over the last N lines for EVENT_JSON entries
        for line in lines[-limit:]:
            idx = line.find("EVENT_JSON ")
            if idx != -1:
                payload = line[idx + len("EVENT_JSON "):].strip()
                try:
                    evt = json.loads(payload)
                    events.append(evt)
                except json.JSONDecodeError:
                    # ignore malformed structured events
                    continue
    except FileNotFoundError:
        logger.warning("scancare.log not found when fetching logs.")
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return jsonify({"error": "Failed to read logs."}), 500

    return jsonify({"events": events})

if __name__ == '__main__':
    # Bind to the PORT environment variable for container platforms (defaults to 8080)
    port = int(os.environ.get("PORT", 8080))
    # Listen on all interfaces so Cloud Run can reach the container
    app.run(host="0.0.0.0", port=port, debug=True)