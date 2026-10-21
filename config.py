"""
Configuration file for the Job Application Automation Tool
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration - Using AI Models
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  # gemini, ollama, huggingface
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Google Gemini API key
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')  # gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')  # llama2, mistral, codellama, etc.
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')  # Optional if using HF Inference API

# Google Drive Configuration
GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_DRIVE_TOKEN_FILE = 'token.json'

# Application Settings
OUTPUT_FOLDER = 'outputs'

# Job Match Thresholds
EXCELLENT_MATCH = 80
GOOD_MATCH = 60
FAIR_MATCH = 40

