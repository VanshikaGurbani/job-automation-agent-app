# AI Job Application Automation Tool

An intelligent automation tool that tailors your resume, generates custom cover letters, and provides job match ratings using **Google Gemini AI** for maximum accuracy and ATS optimization.

## Features

- 📝 **Job intake**: Paste a job description or upload a CSV (no job-board scraping)
- 📝 **AI Resume Tailor**: Fine-tune your resume for each specific job with 90%+ ATS match
- 🎨 **LaTeX Resume Support**: Upload your LaTeX template - formatting preserved, only Core Skills modified!
- ✍️ **AI Cover Letter Generator**: Create personalized, keyword-optimized cover letters
- 📊 **Job Match Rating**: Get AI-powered compatibility scores for each job
- ☁️ **Google Drive Integration**: Automatically store generated documents with smart naming
- 🚀 **Google Gemini AI**: Uses latest Gemini 2.5 Flash for maximum accuracy
- 💻 **Streamlit UI**: Beautiful, user-friendly interface
- 📄 **PDF Generation**: LaTeX resumes automatically compiled to PDF
- 🔄 **Duplicate Prevention**: Smart file naming prevents duplicate uploads

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Gemini API

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy your API key

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# LLM Configuration - Using Google Gemini for best results
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Google Drive (optional)
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials.json
```

**Or** create an `api_key.txt` file with just your Gemini API key:
```
your_api_key_here
```

### 4. Set Up Google Drive API (Optional)

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it (e.g., "Job Application Automation")
4. Click **"Create"**

#### Step 2: Enable Google Drive API
1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on it and press **"Enable"**

#### Step 3: Create OAuth 2.0 Credentials
1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Configure the **OAuth consent screen**:
   - User Type: **External**
   - App name: `Job Application Automation`
   - Add your email as a test user
4. Create **Desktop app** credentials
5. Download the JSON file and save as `credentials.json` in project root

## Usage

### 1. Run the Streamlit App

```bash
streamlit run app.py
```

### 2. Using the App

#### Tab 1: Upload Resume
- Upload your resume (PDF, DOCX, or **LaTeX .tex**)
- For LaTeX: Only the "Core Skills" section will be modified
- Fill in your contact information

#### Tab 2: Add Job / Tab 3: Upload Jobs CSV
- Paste a job description you are legitimately viewing, or
- Upload a CSV with columns title, company, location, description, url

#### Tab 3: Process Jobs
- Select how many jobs to process
- Enable Google Drive upload (optional)
- Click "Process Jobs" and watch the magic happen!

## Project Structure

```
Job Application Automation/
├── app.py                      # Main Streamlit application
├── llm_client.py               # Google Gemini AI client
├── ai_resume_tailor.py         # AI resume tailoring (text formats)
├── latex_resume_tailor.py      # LaTeX resume tailoring (Core Skills only)
├── ai_cover_letter.py          # AI cover letter generator
├── job_matcher.py              # Job match rating calculator
├── google_drive_uploader.py    # Google Drive integration
├── utils.py                    # Utility functions (LaTeX parsing, PDF compilation)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── api_key.txt                 # Gemini API key (alternative to .env)
├── credentials.json            # Google Drive OAuth credentials
├── .env                        # Environment variables (create this)
└── README.md                   # This file
```

## How It Works

1. **Upload Resume**: Upload your base resume (PDF, DOCX, or LaTeX)
2. **Upload Jobs**: Provide job listings by pasting a description or uploading a CSV
3. **AI Processing**: For each job, the AI:
   - Analyzes the job description and your resume
   - Calculates a match rating (0-100)
   - Tailors your resume (LaTeX: only Core Skills section)
   - Generates a custom, keyword-optimized cover letter
4. **Save & Upload**: Documents saved locally and optionally to Google Drive

## Google Drive Integration

### File Naming
- **Resume**: `CompanyName_CV.pdf`
- **Cover Letter**: `CompanyName_CoverLetter.docx`

### Features
- ✅ **Duplicate Prevention**: Won't upload files with same names
- ✅ **PDF Upload**: LaTeX resumes compiled to PDF before upload
- ✅ **Smart Organization**: All files in "Job Applications" folder
- ✅ **One-time Auth**: Authenticate once, works forever

## LaTeX Resume Support

### What's Preserved
- ✅ Document structure and formatting
- ✅ All sections except "Core Skills"
- ✅ Styling, fonts, and layout
- ✅ Professional appearance

### What's Modified
- 🎯 **Only Core Skills section** tailored to job requirements
- 🎯 **ATS optimization** with exact keywords from job description
- 🎯 **Maximum 7 skill categories** to fit one page
- 🎯 **90%+ keyword match** for ATS systems

### Output
- `.tex` file with tailored Core Skills
- Automatically compiled to `.pdf` for upload

## Why Google Gemini?

✅ **Maximum Accuracy** - Latest AI model with 1M+ input tokens
✅ **ATS Optimization** - Perfect for resume and cover letter tailoring
✅ **No Truncation** - Full context processing with 8192 output tokens
✅ **Fast & Reliable** - Consistent, high-quality results
✅ **Cost Effective** - Pay-per-use, no monthly fees

## Troubleshooting

### Gemini API Issues?
```bash
# Check your API key
python -c "from config import GEMINI_API_KEY; print('API Key:', GEMINI_API_KEY[:10] + '...' if GEMINI_API_KEY else 'Not found')"

# Test connection
python -c "from llm_client import LLMClient; client = LLMClient(); print('Status:', client.check_availability())"
```

### Google Drive Authentication Failed?
1. Make sure you added yourself as a test user in OAuth consent screen
2. Delete `token.json` if it exists: `rm token.json`
3. Restart the app and try again

### LaTeX Compilation Issues?
```bash
# Install LaTeX (macOS)
brew install --cask mactex

# Install LaTeX (Ubuntu)
sudo apt-get install texlive-full

# Install LaTeX (Windows)
# Download from https://www.tug.org/texlive/
```

## Advanced Configuration

### Custom Models
You can switch between different Gemini models in your `.env`:
```env
GEMINI_MODEL=gemini-2.5-flash    # Fast, cost-effective (recommended)
GEMINI_MODEL=gemini-2.5-pro      # More capable, higher cost
GEMINI_MODEL=gemini-2.0-flash    # Latest model
```

### Fallback to Open Source
If you prefer free local AI, you can switch to Ollama:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
```

## Tips for Best Results

### Resume Optimization
- Use a LaTeX template for professional formatting
- Keep your base resume comprehensive
- Let AI tailor only the Core Skills section

### Cover Letters
- AI uses exact keywords from job descriptions
- Maintains professional tone while being keyword-rich
- Optimized for ATS systems

### Job Matching
- Scores based on skills, experience, and requirements alignment
- Provides detailed analysis and recommendations
- Helps prioritize which jobs to apply for

## License

MIT License

---

**Ready to automate your job applications? Start with `streamlit run app.py`!** 🚀