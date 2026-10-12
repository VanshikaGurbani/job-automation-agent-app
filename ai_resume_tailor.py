"""
AI Resume Tailor
Uses open-source LLMs to tailor resumes for specific job postings
"""
from llm_client import LLMClient
import config


class AIResumeTailor:
    def __init__(self):
        """Initialize the AI Resume Tailor"""
        self.llm = LLMClient()
    
    def tailor_resume(self, resume_text, job_title, job_description, company_name=""):
        """
        Tailor a resume for a specific job posting
        
        Args:
            resume_text: Original resume content
            job_title: Job title
            job_description: Job description
            company_name: Company name (optional)
        
        Returns:
            str: Tailored resume
        """
        prompt = self._create_resume_prompt(resume_text, job_title, job_description, company_name)
        system_prompt = "You are an expert resume writer and career coach. You specialize in tailoring resumes to match specific job descriptions while maintaining authenticity and highlighting relevant skills and experiences."
        
        try:
            tailored_resume = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            return tailored_resume
            
        except Exception as e:
            print(f"Error tailoring resume: {e}")
            return None
    
    def _create_resume_prompt(self, resume_text, job_title, job_description, company_name):
        """Create a prompt for resume tailoring"""
        prompt = f"""
I need you to tailor the following resume for a specific job application.

**Original Resume:**
{resume_text}

**Target Job Title:** {job_title}
**Company:** {company_name if company_name else "Not specified"}

**Job Description:**
{job_description}

**Instructions:**
1. Analyze the job description and identify key requirements, skills, and qualifications
2. Modify the resume to emphasize relevant experience and skills that match the job requirements
3. Use keywords from the job description naturally throughout the resume
4. Reorder or rephrase bullet points to highlight the most relevant experiences first
5. Maintain the original structure and formatting style of the resume
6. Keep all information truthful - do not add fake experience or skills
7. Optimize for ATS (Applicant Tracking Systems) by using standard section headers and clear formatting
8. Make sure the resume remains concise and professional
9. Highlight quantifiable achievements that relate to the job requirements

**Output Format:**
Provide the complete tailored resume in a clean, well-formatted text format. Use clear section headers (e.g., PROFESSIONAL SUMMARY, EXPERIENCE, EDUCATION, SKILLS) and maintain proper spacing.
"""
        return prompt
    
    def generate_professional_summary(self, resume_text, job_title, job_description):
        """
        Generate a tailored professional summary
        
        Args:
            resume_text: Original resume content
            job_title: Job title
            job_description: Job description
        
        Returns:
            str: Professional summary
        """
        prompt = f"""
Based on the following resume and target job, create a compelling professional summary (2-3 sentences) that highlights the most relevant qualifications for this position.

**Resume:**
{resume_text}

**Target Job:** {job_title}

**Job Description:**
{job_description}

**Instructions:**
1. Focus on the most relevant skills and experiences
2. Use strong action words
3. Include years of experience if mentioned in resume
4. Mention key technical skills or domain expertise relevant to the job
5. Keep it concise and impactful (2-3 sentences maximum)
6. Write in first person without using "I"

Provide only the professional summary, nothing else.
"""
        
        try:
            system_prompt = "You are an expert resume writer specializing in creating compelling professional summaries."
            
            summary = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200
            )
            
            return summary
            
        except Exception as e:
            print(f"Error generating professional summary: {e}")
            return None
    
    def suggest_skills(self, resume_text, job_description):
        """
        Suggest additional skills to highlight based on job description
        
        Args:
            resume_text: Original resume content
            job_description: Job description
        
        Returns:
            list: List of suggested skills to emphasize
        """
        prompt = f"""
Analyze this resume and job description to suggest which skills from the resume should be emphasized or highlighted for this specific job.

**Resume:**
{resume_text}

**Job Description:**
{job_description}

**Instructions:**
1. Identify skills mentioned in the resume that are also relevant to the job description
2. Prioritize technical skills, tools, and methodologies mentioned in the job posting
3. Include both hard skills and relevant soft skills
4. List only skills that are actually present in the resume
5. Provide 8-12 most relevant skills

Provide the skills as a comma-separated list, nothing else.
"""
        
        try:
            system_prompt = "You are an expert at matching candidate skills with job requirements."
            
            skills_text = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=200
            )
            
            skills = [skill.strip() for skill in skills_text.split(',')]
            return skills
            
        except Exception as e:
            print(f"Error suggesting skills: {e}")
            return []


# Example usage
if __name__ == "__main__":
    # This is just for testing
    tailor = AIResumeTailor()
    
    sample_resume = """
    John Doe
    Software Engineer
    
    EXPERIENCE:
    - Developed web applications using Python and JavaScript
    - Worked with databases and APIs
    - Collaborated with cross-functional teams
    
    SKILLS:
    Python, JavaScript, SQL, Git
    """
    
    sample_job_desc = """
    We are looking for a Senior Python Developer with experience in:
    - Django framework
    - RESTful API development
    - PostgreSQL
    - AWS deployment
    """
    
    print("Testing AI Resume Tailor...")
    result = tailor.tailor_resume(sample_resume, "Senior Python Developer", sample_job_desc)
    if result:
        print("\nTailored Resume:")
        print(result)

