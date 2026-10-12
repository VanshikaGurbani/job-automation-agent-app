"""
Streamlit Application for AI Job Application Automation
Main UI that brings together all components
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Import custom modules
from linkedin_scraper import LinkedInScraper
from ai_resume_tailor import AIResumeTailor
from latex_resume_tailor import LaTeXResumeTailor
from ai_cover_letter import AICoverLetterGenerator
from job_matcher import JobMatcher
from google_drive_uploader import GoogleDriveUploader
from llm_client import LLMClient
from utils import read_resume, save_to_file, format_filename, create_output_folder, compile_latex_to_pdf
import config


# Page configuration
st.set_page_config(
    page_title="AI Job Application Automation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .match-score {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = None
    if 'resume_latex' not in st.session_state:
        st.session_state.resume_latex = None
    if 'is_latex' not in st.session_state:
        st.session_state.is_latex = False
    if 'jobs_df' not in st.session_state:
        st.session_state.jobs_df = None
    if 'processed_jobs' not in st.session_state:
        st.session_state.processed_jobs = []
    if 'drive_authenticated' not in st.session_state:
        st.session_state.drive_authenticated = False
    if 'applicant_info' not in st.session_state:
        st.session_state.applicant_info = {}


def display_header():
    """Display main header"""
    st.markdown('<h1 class="main-header">🚀 AI Job Application Automation</h1>', unsafe_allow_html=True)
    st.markdown("---")


def sidebar_config():
    """Sidebar configuration and settings"""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Applicant Information
        st.subheader("👤 Your Information")
        name = st.text_input("Full Name", value=st.session_state.applicant_info.get('name', ''))
        email = st.text_input("Email", value=st.session_state.applicant_info.get('email', ''))
        phone = st.text_input("Phone", value=st.session_state.applicant_info.get('phone', ''))
        
        st.session_state.applicant_info = {
            'name': name,
            'email': email,
            'phone': phone
        }
        
        st.markdown("---")
        
        # LLM Configuration
        st.subheader("🤖 LLM Status")
        llm_client = LLMClient()
        if llm_client.is_available():
            st.success(f"✓ {config.LLM_PROVIDER.title()} is running")
            if config.LLM_PROVIDER == 'gemini':
                st.info(f"Model: {config.GEMINI_MODEL}")
            else:
                st.info(f"Model: {config.OLLAMA_MODEL}")
        else:
            st.error(f"✗ {config.LLM_PROVIDER.title()} not available")
            if config.LLM_PROVIDER == 'gemini':
                st.info("Check GEMINI_API_KEY in .env")
            else:
                st.info("Start Ollama: 'ollama serve'")
                st.info(f"Pull model: 'ollama pull {config.OLLAMA_MODEL}'")
        
        st.markdown("---")
        
        # Google Drive Authentication
        st.subheader("☁️ Google Drive")
        if st.button("Authenticate Google Drive"):
            with st.spinner("Authenticating..."):
                uploader = GoogleDriveUploader()
                if uploader.authenticate():
                    st.session_state.drive_authenticated = True
                    st.success("✓ Authenticated!")
                else:
                    st.error("✗ Authentication failed")
        
        if st.session_state.drive_authenticated:
            st.success("✓ Google Drive ready")
        
        st.markdown("---")
        
        # Output folder
        st.subheader("📁 Output")
        output_folder = create_output_folder()
        st.info(f"Files saved to: {output_folder}")


def tab_upload_resume():
    """Tab for uploading resume"""
    st.header("📄 Upload Your Resume")
    
    st.info("💡 **LaTeX Support**: Upload your .tex resume template! The AI will preserve your formatting.")
    
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or LaTeX)",
        type=['pdf', 'docx', 'doc', 'tex'],
        help="Upload your base resume. LaTeX templates will be preserved during tailoring."
    )
    
    if uploaded_file:
        with st.spinner("Reading resume..."):
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'tex':
                # Handle LaTeX resume
                result = read_resume(uploaded_file, return_raw_latex=True)
                if result and len(result) == 2:
                    resume_text, raw_latex = result
                    st.session_state.resume_text = resume_text
                    st.session_state.resume_latex = raw_latex
                    st.session_state.is_latex = True
                    st.success("✓ LaTeX resume uploaded successfully!")
                    st.info("🎨 Your LaTeX template structure will be preserved during tailoring.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander("View Parsed Content"):
                            st.text_area("Parsed Text", resume_text, height=300)
                    with col2:
                        with st.expander("View LaTeX Source"):
                            st.code(raw_latex[:1000] + "..." if len(raw_latex) > 1000 else raw_latex, language="latex")
                else:
                    st.error("Failed to read LaTeX file. Please check the file format.")
            else:
                # Handle PDF/DOCX resume
                resume_text = read_resume(uploaded_file)
                
                if resume_text:
                    st.session_state.resume_text = resume_text
                    st.session_state.resume_latex = None
                    st.session_state.is_latex = False
                    st.success("✓ Resume uploaded successfully!")
                    
                    with st.expander("View Resume Content"):
                        st.text_area("Resume Text", resume_text, height=300)
                else:
                    st.error("Failed to read resume. Please try another file.")


def tab_scrape_jobs():
    """Tab for scraping LinkedIn jobs"""
    st.header("🔍 Scrape LinkedIn Jobs")
    
    st.warning("⚠️ **Note:** LinkedIn scraping may have ChromeDriver issues on some systems (especially macOS).")
    st.info("💡 **Recommended:** Use the **'Upload Jobs CSV'** tab instead for better reliability! See `sample_jobs.csv` for template.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_title = st.text_input("Job Title", value="Software Engineer")
    
    with col2:
        location = st.text_input("Location", value="United States")
    
    with col3:
        num_pages = st.number_input("Number of Pages", min_value=1, max_value=20, value=5)
    
    if st.button("Start Scraping"):
        if not job_title:
            st.error("Please enter a job title")
            return
        
        with st.spinner("Opening browser... Please log in to LinkedIn when prompted."):
            scraper = LinkedInScraper(headless=False)
            
            try:
                scraper.setup_driver()
                scraper.login_prompt()
                
                with st.spinner(f"Scraping jobs for '{job_title}' in '{location}'..."):
                    scraper.scrape_jobs(job_title, location, num_pages)
                    
                    if scraper.jobs_data:
                        scraper.save_to_csv()
                        st.session_state.jobs_df = pd.DataFrame(scraper.jobs_data)
                        st.success(f"✓ Scraped {len(scraper.jobs_data)} jobs!")
                    else:
                        st.warning("No jobs found. Try different search parameters.")
            
            except Exception as e:
                st.error(f"Error during scraping: {e}")
                st.info("💡 **Solution:** Try using the 'Upload Jobs CSV' tab instead!")
                st.info("📖 See `FIX_SCRAPER.md` for detailed troubleshooting steps.")
                
                with st.expander("Quick Fix Options"):
                    st.markdown("""
                    ### Option 1: Use CSV Upload (Easiest!)
                    1. Go to **'Upload Jobs CSV'** tab
                    2. Use `sample_jobs.csv` as a template
                    3. Add your job listings manually
                    4. Upload and process!
                    
                    ### Option 2: Fix ChromeDriver (macOS)
                    ```bash
                    brew install chromedriver
                    xattr -d com.apple.quarantine $(which chromedriver)
                    ```
                    
                    Then try scraping again.
                    
                    See `FIX_SCRAPER.md` for more solutions.
                    """)
            
            finally:
                scraper.close()
    
    # Display scraped jobs
    if st.session_state.jobs_df is not None:
        st.subheader("Scraped Jobs")
        st.dataframe(st.session_state.jobs_df, use_container_width=True)
        
        # Download button
        csv = st.session_state.jobs_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def tab_upload_jobs():
    """Tab for uploading jobs CSV"""
    st.header("📊 Upload Jobs CSV")
    
    st.success("✨ **Recommended Method** - Most reliable and gives you full control!")
    st.info("📝 Use `sample_jobs.csv` as a template. Required columns: title, company, location, description, url")
    
    # Show example format
    with st.expander("📋 View CSV Format Example"):
        st.code("""title,company,location,description,url
Software Engineer,Google,Mountain View,Looking for software engineer with Python...,https://linkedin.com/jobs/123
Data Scientist,Meta,Remote,Seeking data scientist with ML experience...,https://linkedin.com/jobs/456""", language="csv")
    
    uploaded_file = st.file_uploader(
        "Upload Jobs CSV",
        type=['csv'],
        help="CSV should contain job details with the columns shown above"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.jobs_df = df
            st.success(f"✓ Loaded {len(df)} jobs!")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")


def tab_process_jobs():
    """Tab for processing jobs with AI"""
    st.header("🤖 Process Jobs with AI")
    
    # Check prerequisites
    if st.session_state.resume_text is None:
        st.warning("⚠️ Please upload your resume first (Tab 1)")
        return
    
    if st.session_state.jobs_df is None or len(st.session_state.jobs_df) == 0:
        st.warning("⚠️ Please scrape or upload jobs first (Tab 2 or 3)")
        return
    
    # Check LLM availability
    llm_client = LLMClient()
    if not llm_client.is_available():
        st.error(f"⚠️ {config.LLM_PROVIDER.title()} is not available. Please start it first.")
        st.info(f"Run: ollama serve (then: ollama pull {config.OLLAMA_MODEL})")
        return
    
    st.success("✓ Ready to process jobs!")
    
    # Settings
    col1, col2 = st.columns(2)
    
    with col1:
        process_count = st.number_input(
            "Number of jobs to process",
            min_value=1,
            max_value=len(st.session_state.jobs_df),
            value=min(5, len(st.session_state.jobs_df))
        )
    
    with col2:
        upload_to_drive = st.checkbox(
            "Upload to Google Drive",
            value=st.session_state.drive_authenticated
        )
    
    if st.button("🚀 Start Processing", type="primary"):
        # Initialize AI modules
        if st.session_state.is_latex:
            resume_tailor = LaTeXResumeTailor()
        else:
            resume_tailor = AIResumeTailor()
        
        cover_letter_gen = AICoverLetterGenerator()
        job_matcher = JobMatcher()
        
        if upload_to_drive:
            drive_uploader = GoogleDriveUploader()
            if not st.session_state.drive_authenticated:
                print("\n🔐 Authenticating with Google Drive...")
                if drive_uploader.authenticate():
                    st.session_state.drive_authenticated = True
                    print("   ✓ Google Drive authenticated successfully!")
                else:
                    st.error("❌ Google Drive authentication failed. Files will be saved locally only.")
                    upload_to_drive = False
            else:
                # Re-authenticate even if session says authenticated (uploader is new)
                if not drive_uploader.authenticate():
                    st.error("❌ Google Drive authentication failed. Files will be saved locally only.")
                    upload_to_drive = False
        
        # Process each job
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_results = []
        
        for idx, row in st.session_state.jobs_df.head(process_count).iterrows():
            job_title = str(row.get('title', 'Unknown')) if row.get('title') else 'Unknown'
            company = str(row.get('company', 'Unknown')) if row.get('company') else 'Unknown'
            description = str(row.get('description', '')) if row.get('description') and str(row.get('description')) != 'nan' else ''
            
            # Print beautiful header
            print("\n" + "="*80)
            print(f"📋 JOB {idx + 1}/{process_count}")
            print("="*80)
            print(f"🏢 Company:  {company}")
            print(f"💼 Position: {job_title}")
            print("-"*80)
            
            status_text.text(f"Processing {idx + 1}/{process_count}: {job_title} at {company}")
            
            # Skip jobs with no description
            if not description.strip():
                print(f"⚠️  SKIPPED: No job description available")
                st.warning(f"⚠️ Skipping {job_title} at {company} - no description available")
                continue
            
            # Calculate match score
            print(f"\n🎯 STEP 1: Analyzing Job Match...")
            match_result = job_matcher.calculate_match_score(
                st.session_state.resume_text,
                job_title,
                description
            )
            print(f"   ✓ Match Score: {match_result['overall_score']:.0f}% ({match_result['match_level']})")
            
            # Tailor resume
            print(f"\n📝 STEP 2: Tailoring Resume...")
            if st.session_state.is_latex:
                tailored_resume = resume_tailor.tailor_latex_resume(
                    st.session_state.resume_latex,
                    st.session_state.resume_text,
                    job_title,
                    description,
                    company
                )
            else:
                tailored_resume = resume_tailor.tailor_resume(
                    st.session_state.resume_text,
                    job_title,
                    description,
                    company
                )
            
            # Generate cover letter
            print(f"\n✍️  STEP 3: Generating Cover Letter...")
            cover_letter = cover_letter_gen.generate_cover_letter(
                st.session_state.resume_text,
                job_title,
                description,
                company,
                st.session_state.applicant_info.get('name', ''),
                st.session_state.applicant_info.get('email', ''),
                st.session_state.applicant_info.get('phone', '')
            )
            print(f"   ✓ Cover letter generated ({len(cover_letter) if cover_letter else 0} chars)")
            
            # Save files
            print(f"\n💾 STEP 4: Saving Documents...")
            pdf_path = None
            if st.session_state.is_latex:
                resume_filename = format_filename(company, job_title, 'resume.tex')
                resume_path = save_to_file(tailored_resume, resume_filename)
                print(f"   ✓ LaTeX saved: {resume_filename}")
                
                # Compile LaTeX to PDF
                pdf_path = compile_latex_to_pdf(resume_path)
                if pdf_path:
                    print(f"   ✓ PDF compiled: {os.path.basename(pdf_path)}")
                else:
                    print("   ⚠️  PDF compilation skipped (pdflatex not available)")
            else:
                resume_filename = format_filename(company, job_title, 'resume.txt')
                resume_path = save_to_file(tailored_resume, resume_filename)
                print(f"   ✓ Resume saved: {resume_filename}")
            
            cover_filename = format_filename(company, job_title, 'cover_letter.docx')
            cover_path = save_to_file(cover_letter, cover_filename)
            if cover_path:
                print(f"   ✓ Cover letter saved: {cover_filename}")
            
            # Upload to Drive if enabled (only if files were saved)
            drive_links = None
            if upload_to_drive and st.session_state.drive_authenticated and cover_path:
                print(f"\n☁️  STEP 5: Uploading to Google Drive...")
                try:
                    # Upload PDF if available, otherwise upload the resume_path
                    upload_resume_path = pdf_path if pdf_path else resume_path
                    drive_links = drive_uploader.upload_application_documents(
                        upload_resume_path,
                        cover_path,
                        company,
                        job_title
                    )
                    print(f"   ✓ Files uploaded to Drive")
                except Exception as e:
                    print(f"   ✗ Upload failed: {e}")
                    st.warning(f"Failed to upload to Drive: {e}")
            
            processed_results.append({
                'job_title': job_title,
                'company': company,
                'match_score': match_result['overall_score'],
                'match_level': match_result['match_level'],
                'resume_file': resume_filename,
                'cover_letter_file': cover_filename,
                'analysis': match_result
            })
            
            print(f"\n✅ COMPLETED: {company} - {job_title}")
            print("="*80 + "\n")
            
            progress_bar.progress((idx + 1) / process_count)
        
        st.session_state.processed_jobs = processed_results
        status_text.text("✓ Processing complete!")
        st.success(f"Successfully processed {len(processed_results)} jobs!")
        st.balloons()


def tab_results():
    """Tab for viewing results"""
    st.header("📊 Results & Analysis")
    
    if not st.session_state.processed_jobs:
        st.info("No processed jobs yet. Go to 'Process Jobs' tab to start!")
        return
    
    # Create results dataframe
    results_df = pd.DataFrame([
        {
            'Job Title': job['job_title'],
            'Company': job['company'],
            'Match Score': job['match_score'],
            'Match Level': job['match_level']
        }
        for job in st.session_state.processed_jobs
    ])
    
    # Sort by match score
    results_df = results_df.sort_values('Match Score', ascending=False)
    
    # Display summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_score = results_df['Match Score'].mean()
        st.metric("Average Match Score", f"{avg_score:.1f}/100")
    
    with col2:
        best_match = results_df.iloc[0]
        st.metric("Best Match", f"{best_match['Match Score']:.0f}/100", 
                 delta=best_match['Company'])
    
    with col3:
        excellent_matches = len(results_df[results_df['Match Score'] >= config.EXCELLENT_MATCH])
        st.metric("Excellent Matches", excellent_matches)
    
    st.markdown("---")
    
    # Display results table
    st.subheader("All Jobs")
    st.dataframe(results_df, use_container_width=True)
    
    # Detailed view for each job
    st.subheader("Detailed Analysis")
    
    for job in st.session_state.processed_jobs:
        with st.expander(f"{job['company']} - {job['job_title']} (Score: {job['match_score']}/100)"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Match score display
                score_color = "green" if job['match_score'] >= config.GOOD_MATCH else "orange" if job['match_score'] >= config.FAIR_MATCH else "red"
                st.markdown(f"<div class='match-score' style='color: {score_color};'>{job['match_score']}</div>", 
                          unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>{job['match_level']}</div>", 
                          unsafe_allow_html=True)
            
            with col2:
                analysis = job['analysis']
                
                st.markdown("**Summary:**")
                st.info(analysis.get('summary', 'No summary available'))
                
                st.markdown("**Strengths:**")
                for strength in analysis.get('strengths', []):
                    st.markdown(f"✓ {strength}")
                
                st.markdown("**Areas to Address:**")
                for gap in analysis.get('gaps', []):
                    st.markdown(f"⚠️ {gap}")
                
                st.markdown("**Recommendations:**")
                for rec in analysis.get('recommendations', []):
                    st.markdown(f"→ {rec}")
            
            # File links
            st.markdown("**Generated Documents:**")
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"📄 Resume: {job['resume_file']}")
            with col2:
                st.text(f"✉️ Cover Letter: {job['cover_letter_file']}")


def main():
    """Main application"""
    init_session_state()
    display_header()
    sidebar_config()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Upload Resume",
        "🔍 Scrape Jobs",
        "📊 Upload Jobs CSV",
        "🤖 Process Jobs",
        "📊 Results"
    ])
    
    with tab1:
        tab_upload_resume()
    
    with tab2:
        tab_scrape_jobs()
    
    with tab3:
        tab_upload_jobs()
    
    with tab4:
        tab_process_jobs()
    
    with tab5:
        tab_results()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            AI Job Application Automation Tool | Built with Streamlit & OpenAI
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

