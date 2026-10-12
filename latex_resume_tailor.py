"""
LaTeX Resume Tailor
Tailors LaTeX resumes while preserving template structure and formatting
"""
import re
from llm_client import LLMClient
import config


class LaTeXResumeTailor:
    def __init__(self):
        """Initialize the LaTeX Resume Tailor"""
        self.llm = LLMClient()
    
    def tailor_latex_resume(self, latex_template, resume_text, job_title, 
                           job_description, company_name=""):
        """
        Tailor a LaTeX resume - ONLY modifies Core Skills section
        
        Args:
            latex_template: Original LaTeX source code
            resume_text: Parsed text from LaTeX (for AI understanding)
            job_title: Job title
            job_description: Job description
            company_name: Company name
        
        Returns:
            str: Tailored LaTeX source code with only Core Skills modified
        """
        
        # Extract ONLY the Core Skills section
        skills_section = self._extract_core_skills(latex_template)
        
        if not skills_section:
            print("  Warning: Could not find Core Skills section")
            return latex_template
        
        # Tailor only the skills section
        try:
            tailored_skills = self._tailor_core_skills(
                skills_section,
                job_title,
                job_description,
                company_name
            )
        except Exception as e:
            print(f"  ✗ ERROR tailoring skills: {e}")
            print(f"  ℹ️ Using original skills section")
            return latex_template
        
        if not tailored_skills:
            print("  ⚠️ No tailored skills returned, keeping original")
            return latex_template
        
        print(f"   ✓ Resume tailored (Core Skills updated)")
        
        # Replace only the Core Skills section in the original template
        tailored_latex = self._replace_core_skills(latex_template, tailored_skills)
        
        return tailored_latex
    
    def _extract_core_skills(self, latex_content):
        """Extract only the Core Skills section"""
        # Pattern to match Core Skills section
        pattern = r'(\\section\*?\{Core Skills\}.*?)(\\end\{document\})'
        match = re.search(pattern, latex_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Return everything from \section{Core Skills} to \end{document}
            skills_content = match.group(1)
            
            # Check if there's a \begin{small} wrapper
            if '\\begin{small}' in skills_content:
                # Extract itemize inside small environment
                small_pattern = r'\\begin\{small\}\s*(\\begin\{itemize\}.*?\\end\{itemize\})\s*\\end\{small\}'
                small_match = re.search(small_pattern, skills_content, re.DOTALL)
                if small_match:
                    # Return itemize with small wrapper info
                    return small_match.group(1)
            
            # If no small wrapper, just get itemize
            itemize_pattern = r'(\\begin\{itemize\}.*?\\end\{itemize\})'
            itemize_match = re.search(itemize_pattern, skills_content, re.DOTALL)
            if itemize_match:
                return itemize_match.group(1)
        
        return None
    
    def _tailor_core_skills(self, skills_section, job_title, job_description, company_name):
        """Tailor Core Skills with AGGRESSIVE ATS optimization for 90%+ keyword match"""
        try:
            print(f"      🤖 Using AI to tailor Core Skills...")
            
            # Extract keywords from FULL job description (no truncation!)
            import re
            job_keywords = set(re.findall(r'\b(?:Python|Java|SQL|AWS|PyTorch|TensorFlow|Spark|Kubernetes|Docker|[A-Z][a-z]+)\b', job_description))
            top_keywords = ', '.join(list(job_keywords)[:30])  # More keywords for accuracy
            
            # Send FULL context - we have 1M input tokens!
            ats_prompt = f"""Rewrite the Core Skills section for maximum ATS match (90%+) for this {job_title} role.

**Critical Keywords from Job:** {top_keywords}

**Full Job Description:**
{job_description}

**Current Core Skills:**
{skills_section}

**Requirements:**
1. Output ONLY LaTeX: \\begin{{itemize}}[leftmargin=*] ... \\end{{itemize}}
2. Max 7 categories to fit ONE page
3. Use EXACT keywords from job description above
4. Put most relevant skills FIRST
5. Each category: \\item \\textbf{{Category Name:}} skill1, skill2, skill3, skill4
6. Remove ANY skill not mentioned in job description
7. NO explanations, NO markdown, ONLY LaTeX code

Output the complete itemize block:"""
            
            tailored = self.llm.generate(
                ats_prompt,
                system_prompt="You are an ATS optimization expert. Output ONLY valid LaTeX code to maximize keyword match.",
                temperature=0.3,  # Low for keyword focus
                max_tokens=8192  # MAXIMUM for Gemini 2.5 Flash
            )
            
            if not tailored or len(tailored) < 50:
                print(f"  ⚠️ Empty/blocked response, keeping original")
                return None
            
            print(f"      ✓ AI response received ({len(tailored)} chars)")
            
            # Clean up the response aggressively
            tailored = re.sub(r'```latex\n?', '', tailored)
            tailored = re.sub(r'```\n?', '', tailored)
            tailored = tailored.strip()
            
            # Extract only the itemize block if there's extra text
            itemize_pattern = r'(\\begin\{itemize\}.*?\\end\{itemize\})'
            itemize_match = re.search(itemize_pattern, tailored, re.DOTALL)
            if itemize_match:
                tailored = itemize_match.group(1)
            
            # Remove any text after \end{itemize}
            end_pos = tailored.find('\\end{itemize}')
            if end_pos != -1:
                tailored = tailored[:end_pos + len('\\end{itemize}')]
            
            # Remove any text before \begin{itemize}
            begin_pos = tailored.find('\\begin{itemize}')
            if begin_pos != -1:
                tailored = tailored[begin_pos:]
            
            # Verify it's valid LaTeX itemize
            if '\\begin{itemize}' in tailored and '\\end{itemize}' in tailored:
                # Ensure no explanatory text leaked through
                if 'I have' in tailored or 'reordered' in tailored or 'emphasized' in tailored:
                    print("  Warning: AI added explanatory text, cleaning...")
                    # Try to extract just the itemize content
                    lines = tailored.split('\n')
                    clean_lines = [line for line in lines if line.strip().startswith('\\item') or 
                                 '\\begin{itemize}' in line or '\\end{itemize}' in line]
                    tailored = '\n'.join(clean_lines)
                
                return tailored
            else:
                print("  Warning: AI output doesn't contain valid itemize structure")
                return None
            
        except Exception as e:
            print(f"  Error tailoring core skills: {e}")
            return None
    
    def _replace_core_skills(self, latex_template, new_skills_section):
        """Replace only the Core Skills itemize section in the template"""
        # Ensure new_skills_section doesn't have extra text
        new_skills_section = new_skills_section.strip()
        
        # Check if original has \begin{small} wrapper
        has_small_wrapper = '\\begin{small}' in latex_template and \
                           latex_template.find('\\begin{small}') < latex_template.find('\\section*{Core Skills}') + 200
        
        if has_small_wrapper:
            # Find and replace the itemize block inside small environment
            pattern = r'(\\section\*?\{Core Skills\}.*?\\begin\{small\}\s*)(\\begin\{itemize\}.*?\\end\{itemize\})(\s*\\end\{small\}.*?\\end\{document\})'
            
            def replace_skills(match):
                before = match.group(1)
                after = match.group(3)
                return before + new_skills_section + after
            
            result = re.sub(pattern, replace_skills, latex_template, flags=re.DOTALL | re.IGNORECASE)
        else:
            # No small wrapper, replace itemize directly
            pattern = r'(\\section\*?\{Core Skills\}.*?)(\\begin\{itemize\}.*?\\end\{itemize\})(.*?\\end\{document\})'
            
            def replace_skills(match):
                before = match.group(1)
                after = match.group(3)
                return before + new_skills_section + after
            
            result = re.sub(pattern, replace_skills, latex_template, flags=re.DOTALL | re.IGNORECASE)
        
        # Verify no extra text was added after \end{document}
        if 'I have reordered' in result or 'I have also added' in result or 'Certainly' in result:
            print("  WARNING: Extra text detected in output, cleaning...")
            # Remove everything after \end{document}
            doc_end = result.find('\\end{document}')
            if doc_end != -1:
                result = result[:doc_end + len('\\end{document}')]
        
        return result
    
    def _tailor_section(self, section_name, section_content, full_resume_text,
                       job_title, job_description, company_name):
        """Tailor a specific section of the resume"""
        
        # Determine if this section should be tailored
        relevant_sections = ['experience', 'summary', 'objective', 'skills', 
                           'projects', 'achievements', 'professional']
        
        should_tailor = any(keyword in section_name.lower() for keyword in relevant_sections)
        
        if not should_tailor:
            return section_content
        
        prompt = f"""You are helping tailor a LaTeX resume for a job application. 

**Job Title:** {job_title}
**Company:** {company_name if company_name else "Not specified"}

**Job Description:**
{job_description[:1000]}

**Current Resume Section ({section_name}):**
{section_content}

**Instructions:**
1. Modify the LaTeX code to better align with the job requirements
2. PRESERVE all LaTeX commands, formatting, and structure
3. Only change the text content within the LaTeX commands
4. Emphasize relevant skills and experiences mentioned in the job description
5. Use keywords from the job description naturally
6. Keep all bullet points, itemize environments, and formatting intact
7. Do not add or remove major structural elements
8. Keep the changes truthful to the original content

**Output:**
Provide ONLY the modified LaTeX code for this section, nothing else. Do not include explanations or markdown code blocks.
"""
        
        try:
            system_prompt = "You are an expert resume writer and LaTeX specialist. You tailor resume content while preserving LaTeX formatting."
            
            tailored = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.6
            )
            
            # Clean up the response (remove markdown if present)
            tailored = re.sub(r'```latex\n?', '', tailored)
            tailored = re.sub(r'```\n?', '', tailored)
            tailored = tailored.strip()
            
            return tailored
            
        except Exception as e:
            print(f"Error tailoring section {section_name}: {e}")
            return section_content
    
    def _reconstruct_latex(self, original_latex, tailored_sections):
        """Reconstruct LaTeX document with tailored sections"""
        result = original_latex
        
        for section_name, tailored_content in tailored_sections.items():
            # Find and replace the section in the original document
            if section_name == 'Summary':
                # Handle summary/objective differently
                pattern = r'(\\textbf\{.*?Summary.*?\}.*?)(?=\\section|\\begin)'
                result = re.sub(pattern, tailored_content, result, 
                              flags=re.DOTALL | re.IGNORECASE)
            else:
                # Handle regular sections
                pattern = r'(\\section\*?\{' + re.escape(section_name) + r'\})(.*?)(?=\\section|\\end\{document\}|$)'
                
                def replace_section(match):
                    return match.group(1) + '\n' + tailored_content
                
                result = re.sub(pattern, replace_section, result, 
                              flags=re.DOTALL | re.IGNORECASE)
        
        return result
    
    def generate_latex_summary(self, resume_text, job_title, job_description):
        """
        Generate a professional summary in LaTeX format
        
        Args:
            resume_text: Resume content
            job_title: Target job title
            job_description: Job description
        
        Returns:
            str: LaTeX formatted professional summary
        """
        prompt = f"""Create a professional summary for a resume targeting this position.

**Target Position:** {job_title}

**Job Description:**
{job_description[:800]}

**Candidate Background:**
{resume_text[:1000]}

**Instructions:**
1. Write 2-3 sentences highlighting the most relevant qualifications
2. Format as LaTeX code suitable for a resume
3. Use \\textbf for emphasis if needed
4. Keep it concise and impactful
5. Focus on skills and experience relevant to the job

**Output:**
Provide ONLY the LaTeX code, nothing else.
Example format:
\\textbf{{Professional Summary}} \\\\
[Your summary text here]
"""
        
        try:
            summary = self.llm.generate(
                prompt,
                system_prompt="You are an expert resume writer who creates compelling professional summaries.",
                temperature=0.7
            )
            
            # Clean up response
            summary = re.sub(r'```latex\n?', '', summary)
            summary = re.sub(r'```\n?', '', summary)
            summary = summary.strip()
            
            return summary
            
        except Exception as e:
            print(f"Error generating LaTeX summary: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    # Sample LaTeX resume
    sample_latex = r"""
\documentclass{article}
\begin{document}

\section{Experience}
\textbf{Software Engineer} \\ 
Acme Corp, 2020-2023
\begin{itemize}
\item Developed web applications using Python and JavaScript
\item Worked with databases and APIs
\item Collaborated with teams
\end{itemize}

\section{Skills}
Python, JavaScript, SQL, Git

\end{document}
"""
    
    print("Testing LaTeX Resume Tailor...")
    tailor = LaTeXResumeTailor()
    
    if tailor.llm.is_available():
        print("✓ LLM is available\n")
        
        job_desc = """
        We are looking for a Senior Python Developer with experience in:
        - Django framework
        - RESTful API development
        - PostgreSQL
        - AWS deployment
        """
        
        print("Extracting sections...")
        sections = tailor._extract_latex_sections(sample_latex)
        print(f"Found sections: {list(sections.keys())}")
    else:
        print("✗ LLM not available. Please start Ollama and pull a model.")
        print("Run: ollama pull llama2")

