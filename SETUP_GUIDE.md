# Quick Setup Guide

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Install and Start Ollama

### macOS:
```bash
brew install ollama
ollama serve
```

### Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

### Windows:
Download installer from https://ollama.ai/

## Step 3: Download an AI Model

Open a new terminal and run:

```bash
# Choose ONE of these models:
ollama pull llama2          # Recommended for beginners (3.8GB)
ollama pull mistral         # Faster alternative (4.1GB)
ollama pull llama2:13b      # More powerful (7.3GB)
```

## Step 4: Create .env File

Create a file named `.env` in the project folder:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

## Step 5: Test Your Setup

```bash
# Test the LLM connection
python llm_client.py
```

You should see "✓ LLM is working correctly!"

## Step 6: Run the App

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Usage Workflow

1. **Upload Your Resume** (Tab 1)
   - Supports PDF, DOCX, or **LaTeX (.tex)** files
   - LaTeX templates will preserve your formatting!

2. **Get Jobs** (Tab 2 or 3)
   - Option A: Scrape LinkedIn (requires manual login)
   - Option B: Upload your own CSV file

3. **Process Jobs** (Tab 4)
   - Select how many jobs to process
   - AI will tailor resumes and write cover letters
   - Each job gets a match rating (0-100)

4. **View Results** (Tab 5)
   - See match ratings and detailed analysis
   - Files saved in `outputs/` folder
   - Optionally upload to Google Drive

## LaTeX Resume Tips

✨ **Your LaTeX template is fully supported!**

- Upload your `.tex` file directly
- The AI preserves your formatting, sections, and style
- Only the content is tailored to match job requirements
- Output files are `.tex` ready to compile

Example LaTeX sections that will be tailored:
- Professional Summary
- Work Experience
- Skills
- Projects

## Troubleshooting

### "Could not connect to Ollama"
1. Make sure Ollama is running: `ollama serve`
2. Check if model is downloaded: `ollama list`
3. If not, pull it: `ollama pull llama2`

### "Service not available"
- Ollama might still be starting up - wait 10 seconds and try again
- Check if port 11434 is available: `lsof -i :11434`

### Slow performance
- Use a smaller model (llama2 instead of llama2:13b)
- Process fewer jobs at once (1-3 instead of 5+)
- Close other applications using RAM/CPU

### LinkedIn scraper not working
- Make sure you're logged in when prompted
- LinkedIn may have rate limits - try again later
- Use CSV upload instead as a backup

## Optional: Google Drive Integration

If you want to auto-upload documents to Google Drive:

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json` in project folder
6. Click "Authenticate Google Drive" in the app sidebar

## Model Recommendations

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| llama2 | 3.8GB | General use, balanced | Fast |
| mistral | 4.1GB | Quick processing | Very Fast |
| llama2:13b | 7.3GB | Complex resumes, better quality | Slower |
| codellama | 3.8GB | Tech/engineering roles | Fast |

## Need Help?

- Check the main README.md for detailed documentation
- Test individual components (see Project Structure in README)
- Make sure all dependencies are installed
- Verify Ollama is running and model is downloaded

## Privacy & Cost

✅ **100% Free** - No API costs, ever
✅ **Private** - All processing happens on your computer
✅ **No Internet Required** - After downloading the model
✅ **Unlimited** - Process as many jobs as you want

Happy job hunting! 🚀

