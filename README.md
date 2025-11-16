# ScanCare: AI-Powered Medical Report Analysis

**Transform your complex medical reports into simple, understandable insights.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Live Application

**Experience ScanCare live! Visit the deployed application:**

### **[https://scancare21-93219103935.asia-south1.run.app/](https://scancare21-93219103935.asia-south1.run.app/)**

---

## 🌟 Overview

ScanCare is an intelligent web application designed to help patients and caregivers understand complex medical reports with ease. By leveraging the power of Google's Gemini AI, ScanCare analyzes uploaded medical documents—such as lab results, radiology reports, and health summaries—and provides clear, jargon-free explanations. Users can interact with the AI through a conversational chat interface to ask follow-up questions, making healthcare more accessible and transparent for everyone.

### Key Features:
- **📄 Multi-Format Upload:** Supports various file types including `.txt`, `.pdf`, `.png`, `.jpg`, and `.docx`.
- **🤖 AI-Powered Analysis:** Uses advanced AI to interpret medical terminology and data.
- **💬 Interactive Chat:** Ask follow-up questions to get personalized and contextual health guidance.
- **🔒 Privacy-First:** Your data is processed securely and is not stored permanently. Files are handled in-memory and deleted after analysis.
- **💻 Modern & Responsive UI:** A clean, intuitive, and mobile-friendly interface designed for a seamless user experience.

---

## 📸 Application Screenshot

*A preview of the ScanCare user interface.*

![ScanCare Screenshot](https://raw.githubusercontent.com/ace-ify/ScanCare21/main/ex.webp)

---

## 🛠️ Tech Stack

- **Backend:** **Flask** (Python)
- **AI Model:** **Google Gemini 2.0 Flash**
- **Frontend:** HTML5, CSS3, JavaScript
- **Deployment:** **Google Cloud Run** with Gunicorn

---

## ⚙️ Local Development Setup

Follow these steps to run ScanCare on your local machine.

### Prerequisites
- Python 3.10+
- A Google Gemini API Key

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ace-ify/ScanCare21.git
    cd ScanCare21
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the root directory and add your Google Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:8080`.

---

## 🚀 Deployment to Google Cloud Run

This application is configured for easy deployment to Google Cloud Run using Buildpacks.

1.  **Authenticate with gcloud:**
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```

2.  **Create a secret for your API key in Secret Manager:**
    ```bash
    gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"
    gcloud secrets versions add GEMINI_API_KEY --data-file=".env"
    ```

3.  **Deploy the application:**
    ```bash
    gcloud run deploy scancare21 \
        --source . \
        --region asia-south1 \
        --allow-unauthenticated \
        --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
        --memory 1Gi \
        --cpu 1
    ```

---

## ⚕️ Medical Disclaimer

**IMPORTANT:** ScanCare is an AI-powered tool intended for informational purposes only. It is **not** a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for any medical concerns or before making any health-related decisions.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/licenses/MIT) file for details.

---

**Built with ❤️ for the Hackathon Community**