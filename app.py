from flask import Flask, request, jsonify, render_template, send_from_directory, session
import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime
import secrets
from werkzeug.utils import secure_filename
from agents import ScanCareWorkflow
from PIL import Image
import base64

# Try to import CORS, but don't fail if it's not available
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    logging.warning("Flask-CORS not available. Install with: pip install Flask-CORS")

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(
    __name__,
    static_folder=os.path.join('templates', 'public'),
    static_url_path='/public'
)

# Enable CORS if available
if CORS_AVAILABLE:
    CORS(app)  # Enable CORS for all routes
else:
    # Manual CORS headers for all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

app.secret_key = secrets.token_hex(32)  # For session management

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

# Initialize ScanCare Multi-Agent System
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("❌ GEMINI_API_KEY not found in environment variables!")
    logger.error("Please add your API key to the .env file")
    scancare_workflow = None
else:
    try:
        scancare_workflow = ScanCareWorkflow(api_key)
        logger.info("✅ ScanCare Multi-Agent System initialized successfully")
        logger.info("🤖 Active agents: Extraction → Analysis → Conversation")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ScanCare workflow: {str(e)}")
        scancare_workflow = None

# Store user workflows per session (use Redis/database in production)
user_workflows = {}


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_workflow():
    """Get or create a workflow instance for the current user session."""
    if scancare_workflow is None:
        return None
    
    # Get or create session ID
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    
    session_id = session['session_id']
    
    # Create workflow for this user if it doesn't exist
    if session_id not in user_workflows:
        user_workflows[session_id] = ScanCareWorkflow(api_key)
        logger.info(f"Created new workflow for session: {session_id[:8]}...")
    
    return user_workflows[session_id]


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
    """Serve assets from templates/public."""
    assets_dir = os.path.join(app.root_path, 'templates', 'public')
    return send_from_directory(assets_dir, filename)


@app.route('/analyze', methods=['POST'])
def analyze_report():
    """
    Multi-agent analysis endpoint for medical reports.
    
    Supports:
    - Text input (JSON with 'report_text')
    - File uploads (txt, pdf, docx, images)
    - Conversational queries (JSON with 'query')
    
    Workflow:
    1. Extract structured data from report
    2. Analyze values and check ranges
    3. Generate comprehensive insights
    4. Maintain context for follow-ups
    """
    
    if scancare_workflow is None:
        return jsonify({
            "error": "ScanCare system not initialized. Please check API key configuration."
        }), 500
    
    try:
        workflow = get_user_workflow()
        if workflow is None:
            return jsonify({"error": "Failed to create workflow session"}), 500
        
        report_text = None
        is_report = False
        analysis_metadata = {}
        
        # Check if this is a file upload
        if 'report_file' in request.files:
            file = request.files['report_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                analysis_metadata['filename'] = filename
                analysis_metadata['file_type'] = filename.split('.')[-1].lower()
                
                # Extract text based on file type
                if filename.lower().endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report_text = f.read()
                    is_report = True
                
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # For images, use basic Gemini vision first to extract text
                    # Then pass to multi-agent workflow
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        
                        # Read image file
                        with open(filepath, 'rb') as img_file:
                            image_data = img_file.read()
                        
                        # Determine correct mime type
                        file_ext = analysis_metadata['file_type'].lower()
                        if file_ext == 'jpg':
                            mime_type = 'image/jpeg'
                        else:
                            mime_type = f'image/{file_ext}'
                        
                        # Create vision model - try experimental first, fallback to stable
                        try:
                            vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                        except Exception as model_err:
                            logger.warning(f"Experimental model not available, using stable: {model_err}")
                            vision_model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        # Extract text from image
                        extract_prompt = """Extract all text from this medical report image. 
                        Preserve the exact values, units, and structure. Output only the extracted text."""
                        
                        # Upload the image data properly
                        response = vision_model.generate_content([
                            extract_prompt,
                            {"mime_type": mime_type, "data": image_data}
                        ])
                        
                        if response and response.text:
                            report_text = response.text
                            is_report = True
                            analysis_metadata['extraction_method'] = 'vision_ocr'
                            logger.info(f"Successfully extracted text from image: {filename}")
                        else:
                            raise Exception("No text extracted from image")
                            
                    except Exception as img_error:
                        logger.error(f"Error processing image: {str(img_error)}")
                        return jsonify({
                            "error": "Failed to process image",
                            "message": f"Image processing error: {str(img_error)}",
                            "hint": "Please ensure the image contains clear, readable text"
                        }), 500
                
                elif filename.lower().endswith(('.pdf', '.docx')):
                    # Note about format support
                    report_text = f"""[{filename}]
                    
PDF and DOCX parsing requires additional libraries (PyPDF2, python-docx).
Please paste the text content or convert to .txt format for full analysis.

However, you can still ask me questions about your report!"""
                    is_report = False
                
                # Clean up uploaded file
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file: {e}")
            else:
                return jsonify({"error": "Invalid file type. Allowed: txt, pdf, docx, png, jpg, jpeg"}), 400
        
        # Check if this is JSON input
        elif request.json:
            data = request.json
            if 'report_text' in data:
                report_text = data['report_text']
                is_report = True
                analysis_metadata['input_type'] = 'text_json'
            elif 'query' in data:
                report_text = data['query']
                is_report = False
                analysis_metadata['input_type'] = 'conversational_query'
        # Also check form data
        elif request.form:
            if 'report_text' in request.form:
                report_text = request.form['report_text']
                is_report = True
                analysis_metadata['input_type'] = 'text_form'
            elif 'query' in request.form:
                report_text = request.form['query']
                is_report = False
                analysis_metadata['input_type'] = 'conversational_form'
        
        if not report_text:
            return jsonify({"error": "Please provide 'report_text', 'query', or upload a 'report_file'."}), 400
        
        logger.info(f"🚀 Processing {'REPORT' if is_report else 'QUERY'} via multi-agent workflow")
        
        # Route through multi-agent workflow
        result = workflow.handle_conversation(report_text, is_report=is_report)
        
        # Structure response based on result type
        if result['type'] == 'report_analysis':
            response_data = {
                "status": "success",
                "analysis_type": "comprehensive_report",
                "workflow_steps": result['workflow_steps'],
                "analysis": result['analysis'],
                "extracted_data": result['extracted_data'],
                "metadata": analysis_metadata,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_system": "multi_agent_workflow"
            }
            
            log_event(
                event_type="MULTI_AGENT_ANALYSIS",
                status="success",
                query=report_text,
                response=result['analysis'],
                metadata={
                    **analysis_metadata,
                    "agents_used": ["extractor", "analyzer"],
                    "workflow_steps": len(result['workflow_steps'])
                }
            )
        
        else:  # conversation type
            response_data = {
                "status": "success",
                "analysis_type": "conversational",
                "response": result['response'],
                "metadata": analysis_metadata,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent_system": "conversational_agent"
            }
            
            log_event(
                event_type="CONVERSATIONAL_QUERY",
                status="success",
                query=report_text,
                response=result['response'],
                metadata=analysis_metadata
            )
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception(f"❌ Error in multi-agent workflow: {e}")
        
        # Get more detailed error info
        error_details = {
            "error_type": type(e).__name__,
            "error": str(e),
            "agent_workflow": True
        }
        
        log_event(
            event_type="ERROR",
            status="error",
            query=report_text if 'report_text' in locals() else None,
            metadata=error_details
        )
        
        # Provide helpful error message
        error_message = str(e)
        if "API" in error_message or "key" in error_message.lower():
            error_message = "API configuration error. Please check your GEMINI_API_KEY."
        elif "rate" in error_message.lower() or "quota" in error_message.lower():
            error_message = "API rate limit reached. Please try again in a moment."
        
        return jsonify({
            "status": "error",
            "error": "Error processing your request",
            "message": error_message,
            "details": error_details if app.debug else None
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    Conversational endpoint for follow-up questions.
    Uses context from previous analysis to provide contextual answers.
    """
    
    if scancare_workflow is None:
        return jsonify({"error": "ScanCare system not initialized"}), 500
    
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Please provide a 'message' field"}), 400
        
        workflow = get_user_workflow()
        if workflow is None:
            return jsonify({"error": "Session not initialized"}), 500
        
        message = data['message']
        logger.info(f"💬 Chat message: {message[:100]}...")
        
        # Use the conversational agent with context
        response = workflow.ask_followup(message)
        
        log_event(
            event_type="FOLLOWUP_CHAT",
            status="success",
            query=message,
            response=response,
            metadata={"has_context": bool(workflow.current_context)}
        )
        
        return jsonify({
            "status": "success",
            "response": response,
            "has_context": bool(workflow.current_context),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        logger.exception(f"❌ Chat error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation history and context for the current session."""
    try:
        workflow = get_user_workflow()
        if workflow:
            workflow.reset()
            logger.info("🔄 Conversation reset")
            return jsonify({
                "status": "success",
                "message": "Conversation reset successfully"
            })
        else:
            return jsonify({"error": "No active session"}), 400
    except Exception as e:
        logger.exception(f"❌ Reset error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Return recent structured events from scancare.log."""
    log_path = os.path.join(os.getcwd(), "scancare.log")
    limit = request.args.get("limit", default=500, type=int)
    events = []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines[-limit:]:
            idx = line.find("EVENT_JSON ")
            if idx != -1:
                payload = line[idx + len("EVENT_JSON "):].strip()
                try:
                    evt = json.loads(payload)
                    events.append(evt)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        logger.warning("scancare.log not found")
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return jsonify({"error": "Failed to read logs"}), 500
    
    return jsonify({"events": events})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "ScanCare Multi-Agent System",
        "agents": {
            "workflow_initialized": scancare_workflow is not None,
            "active_sessions": len(user_workflows)
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


if __name__ == '__main__':
    # Bind to the PORT environment variable (defaults to 8080)
    port = int(os.environ.get("PORT", 8080))
    
    logger.info("=" * 60)
    logger.info("🏥 ScanCare Multi-Agent System Starting...")
    logger.info("=" * 60)
    logger.info(f"🌐 Server: http://0.0.0.0:{port}")
    logger.info(f"🤖 Multi-Agent Workflow: {'✅ Active' if scancare_workflow else '❌ Inactive'}")
    logger.info(f"📁 Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"🔑 API Key: {'✅ Configured' if api_key else '❌ Missing'}")
    logger.info("=" * 60)
    
    # Listen on all interfaces for container platforms
    app.run(host="0.0.0.0", port=port, debug=True)
