"""
Utility functions for the Job Application Automation Tool
"""
import os
import PyPDF2
from docx import Document
import re


def read_pdf(file_path):
    """Read text content from a PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def read_docx(file_path):
    """Read text content from a DOCX file"""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None


def read_latex(file_path):
    """
    Read LaTeX file and return both raw content and parsed text
    
    Args:
        file_path: Path to .tex file
    
    Returns:
        tuple: (raw_latex_content, plain_text_content)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            latex_content = file.read()
        
        # Extract readable text from LaTeX
        import re
        
        text = latex_content
        
        # CRITICAL: Remove everything before \begin{document}
        doc_start = text.find('\\begin{document}')
        if doc_start != -1:
            text = text[doc_start + len('\\begin{document}'):]
        
        # Remove everything after \end{document}
        doc_end = text.find('\\end{document}')
        if doc_end != -1:
            text = text[:doc_end]
        
        # Remove comments
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        
        # Remove all \begin{} and \end{} tags
        text = re.sub(r'\\begin\{[^}]+\}(\[[^\]]*\])?', '', text)
        text = re.sub(r'\\end\{[^}]+\}', '', text)
        
        # Convert sections to headers
        text = re.sub(r'\\section\*?\{([^}]*)\}', r'\n\1:\n', text)
        text = re.sub(r'\\subsection\*?\{([^}]*)\}', r'\n\1:\n', text)
        
        # Remove text formatting but keep content
        text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\href\{[^}]*\}\{([^}]*)\}', r'\1', text)
        
        # Convert \item to bullets
        text = re.sub(r'\\item\s+', '• ', text)
        
        # Remove ALL remaining LaTeX commands
        text = re.sub(r'\\[a-zA-Z@]+\*?(\{[^}]*\})?(\[[^\]]*\])?', '', text)
        text = re.sub(r'\\[^a-zA-Z]', '', text)  # Remove \\ and other escapes
        
        # Remove leftover braces, brackets, backslashes
        text = re.sub(r'[{}[\]\\]', '', text)
        text = re.sub(r'\|', '', text)
        
        # Clean up whitespace aggressively
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = '\n'.join(line.strip() for line in text.split('\n'))
        text = text.strip()
        
        # Final check - if it still has \documentclass, something went wrong
        if '\\documentclass' in text or '\\usepackage' in text:
            print("⚠️ LaTeX parsing failed, returning minimal text")
            # Emergency fallback - just remove most commands
            text = re.sub(r'\\[a-zA-Z]+', '', latex_content)
            text = re.sub(r'[{}\\]', '', text)
            text = clean_text(text)
        
        return latex_content, text
    except Exception as e:
        print(f"Error reading LaTeX file: {e}")
        return None, None


def read_resume(file, return_raw_latex=False):
    """
    Read resume from uploaded file (PDF, DOCX, or LaTeX)
    
    Args:
        file: Streamlit uploaded file object
        return_raw_latex: If True, return tuple of (content, raw_latex) for LaTeX files
    
    Returns:
        str or tuple: Resume text content, or (content, raw_latex) for LaTeX files
    """
    file_extension = file.name.split('.')[-1].lower()
    
    # Save uploaded file temporarily
    temp_path = f"temp_resume.{file_extension}"
    with open(temp_path, 'wb') as f:
        f.write(file.getbuffer())
    
    # Read based on file type
    if file_extension == 'pdf':
        content = read_pdf(temp_path)
        raw_latex = None
    elif file_extension in ['docx', 'doc']:
        content = read_docx(temp_path)
        raw_latex = None
    elif file_extension == 'tex':
        raw_latex, content = read_latex(temp_path)
    else:
        content = None
        raw_latex = None
    
    # Clean up temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    if return_raw_latex and file_extension == 'tex':
        return content, raw_latex
    
    return content


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', '', text)
    
    return text.strip()


def create_output_folder(folder_name='outputs'):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name


def save_to_file(content, filename, folder='outputs'):
    """Save content to a text file"""
    # Handle None or empty content
    if content is None:
        print(f"  ⚠️ Skipping save - no content for {filename}")
        return None
    
    if not isinstance(content, str):
        content = str(content)
    
    if not content.strip():
        print(f"  ⚠️ Skipping save - empty content for {filename}")
        return None
    
    create_output_folder(folder)
    filepath = os.path.join(folder, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def format_filename(company, position, doc_type):
    """
    Format a filename for saving documents
    
    Args:
        company: Company name
        position: Job position
        doc_type: Type of document (resume, cover_letter, resume.tex, etc.)
    
    Returns:
        str: Formatted filename
    """
    # Clean company and position names
    company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')
    position = re.sub(r'[^\w\s-]', '', position).strip().replace(' ', '_')
    
    # Limit filename length to avoid OS issues
    max_len = 100
    company = company[:max_len]
    position = position[:max_len]
    
    return f"{company}_{position}_{doc_type}"


def compile_latex_to_pdf(tex_filepath):
    """
    Compile a LaTeX file to PDF using pdflatex
    
    Args:
        tex_filepath: Path to the .tex file
    
    Returns:
        str: Path to generated PDF, or None if compilation failed
    """
    import subprocess
    import shutil
    
    # Check if pdflatex is available
    if not shutil.which('pdflatex'):
        print("  ⚠️ pdflatex not found. Install MacTeX or TeX Live to compile PDFs.")
        print("     macOS: brew install --cask mactex-no-gui")
        print("     Linux: sudo apt-get install texlive-latex-base")
        return None
    
    try:
        # Get directory and filename
        tex_dir = os.path.dirname(tex_filepath)
        tex_file = os.path.basename(tex_filepath)
        tex_name = os.path.splitext(tex_file)[0]
        
        # Run pdflatex (twice for proper references)
        print(f"  📄 Compiling {tex_file} to PDF...")
        
        # First pass
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tex_dir, tex_filepath],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Second pass for references
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tex_dir, tex_filepath],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if PDF was generated
        pdf_path = os.path.join(tex_dir, f"{tex_name}.pdf")
        
        if os.path.exists(pdf_path):
            print(f"  ✓ PDF generated: {pdf_path}")
            
            # Clean up auxiliary files
            aux_extensions = ['.aux', '.log', '.out']
            for ext in aux_extensions:
                aux_file = os.path.join(tex_dir, f"{tex_name}{ext}")
                if os.path.exists(aux_file):
                    try:
                        os.remove(aux_file)
                    except:
                        pass
            
            return pdf_path
        else:
            print(f"  ✗ PDF compilation failed")
            # Print error log for debugging
            log_file = os.path.join(tex_dir, f"{tex_name}.log")
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    if 'Error' in log_content or 'error' in log_content:
                        print(f"  Check {log_file} for details")
            return None
            
    except subprocess.TimeoutExpired:
        print("  ✗ LaTeX compilation timed out")
        return None
    except Exception as e:
        print(f"  ✗ Error compiling LaTeX: {e}")
        return None


def calculate_keyword_match(resume_text, job_description):
    """
    Calculate keyword match percentage between resume and job description
    
    Args:
        resume_text: Resume content
        job_description: Job description content
    
    Returns:
        float: Match percentage
    """
    # Handle None, NaN, or non-string inputs
    if not isinstance(resume_text, str):
        resume_text = str(resume_text) if resume_text and str(resume_text) != 'nan' else ""
    if not isinstance(job_description, str):
        job_description = str(job_description) if job_description and str(job_description) != 'nan' else ""
    
    # Return 0 if either is empty
    if not resume_text.strip() or not job_description.strip():
        return 0.0
    
    # Extract keywords (simple word frequency approach)
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    job_words = set(re.findall(r'\b\w+\b', job_description.lower()))
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                   'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
                   'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                   'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
    
    resume_words -= common_words
    job_words -= common_words
    
    # Calculate overlap
    if not job_words:
        return 0.0
    
    matching_words = resume_words & job_words
    match_percentage = (len(matching_words) / len(job_words)) * 100
    
    return round(match_percentage, 2)

