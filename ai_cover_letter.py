"""
AI Cover Letter Generator
Uses open-source LLMs to generate personalized cover letters
"""
from llm_client import LLMClient
import config
from datetime import datetime


class AICoverLetterGenerator:
    def __init__(self):
        """Initialize the AI Cover Letter Generator"""
        self.llm = LLMClient()
    
    def generate_cover_letter(self, resume_text, job_title, job_description, 
                             company_name="", applicant_name="", applicant_email="",
                             applicant_phone="", tone="professional"):
        """
        Generate a personalized cover letter
        
        Args:
            resume_text: Resume content
            job_title: Job title
            job_description: Job description
            company_name: Company name
            applicant_name: Applicant's name
            applicant_email: Applicant's email
            applicant_phone: Applicant's phone
            tone: Tone of the letter (professional, enthusiastic, formal)
        
        Returns:
            str: Generated cover letter
        """
        prompt = self._create_cover_letter_prompt(
            resume_text, job_title, job_description, company_name,
            applicant_name, applicant_email, applicant_phone, tone
        )
        
        try:
            # Hyper-targeted for ATS with full context
            cover_letter = self.llm.generate(
                prompt,
                system_prompt="You are an ATS optimization expert. Write keyword-rich cover letters using exact terms from job descriptions.",
                temperature=0.4,  # Lower for keyword focus
                max_tokens=8192  # MAXIMUM for Gemini 2.5 Flash
            )
            
            # If blocked/empty, use fallback
            if not cover_letter or len(cover_letter) < 100:
                print("  ⚠️ Cover letter blocked, using template")
                return self._generate_fallback_cover_letter(applicant_name, job_title, company_name)
            
            return cover_letter
            
        except Exception as e:
            print(f"  ⚠️ Error: {e}, using template")
            return self._generate_fallback_cover_letter(applicant_name, job_title, company_name)
    
    def _generate_fallback_cover_letter(self, name, job_title, company_name):
        """Simple fallback cover letter when AI is blocked"""
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}.

With my background in data science, machine learning, and software engineering, I am confident I can make valuable contributions to your team. My experience with Python, ML frameworks, and data analysis aligns well with this role.

I am excited about the opportunity to bring my skills to {company_name} and would welcome the chance to discuss how I can contribute to your team's success.

Thank you for your consideration.

Best regards,
{name}"""
    
    def _create_cover_letter_prompt(self, resume_text, job_title, job_description,
                                   company_name, applicant_name, applicant_email,
                                   applicant_phone, tone):
        """Create a prompt for cover letter generation"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Extract key requirements from FULL job description
        import re
        job_keywords = re.findall(r'\b(?:Python|Java|SQL|AWS|ML|AI|PyTorch|TensorFlow|Spark|[A-Z][a-z]+(?:Script|Flow|Torch|Learn))\b', job_description)
        key_requirements = ', '.join(list(set(job_keywords))[:20])
        
        prompt = f"""Write a highly targeted cover letter for 90%+ ATS match using EXACT keywords from the job posting.

**Position:** {job_title} at {company_name}
**Key Required Skills:** {key_requirements}

**Complete Job Description:**
{job_description}

**Candidate Background:**
{resume_text}

**Instructions:**
- Use EXACT keywords and phrases from the job description above
- Mirror job posting language (e.g., "PyTorch" not "deep learning frameworks")  
- Keep it professional, 3 paragraphs, ~300 words
- Sound natural while being keyword-optimized

**Format:**
{applicant_name if applicant_name else "[Your Name]"}
{applicant_email if applicant_email else "[Your Email]"} | {applicant_phone if applicant_phone else "[Your Phone]"}

{current_date}

Dear Hiring Manager,

[Write the cover letter]

Sincerely,
{applicant_name if applicant_name else "[Your Name]"}"""
        return prompt
    
    def generate_opening_paragraph(self, job_title, company_name, job_description):
        """
        Generate just the opening paragraph of a cover letter
        
        Args:
            job_title: Job title
            company_name: Company name
            job_description: Job description
        
        Returns:
            str: Opening paragraph
        """
        prompt = f"""
Write a compelling opening paragraph for a cover letter for this position:

**Position:** {job_title}
**Company:** {company_name if company_name else "this company"}
**Job Description:** {job_description[:300]}...

**Instructions:**
1. Express genuine interest and enthusiasm
2. Mention something specific about the company or role (if available)
3. Briefly state why you're a great fit
4. Keep it to 2-3 sentences
5. Make it engaging and personal

Provide only the opening paragraph, nothing else.
"""
        
        try:
            system_prompt = "You are an expert at writing engaging cover letter opening paragraphs."
            
            opening = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=200
            )
            
            return opening
            
        except Exception as e:
            print(f"Error generating opening paragraph: {e}")
            return None
    
    def customize_for_company(self, base_cover_letter, company_name, company_info=""):
        """
        Customize a cover letter for a specific company
        
        Args:
            base_cover_letter: Base cover letter content
            company_name: Company name
            company_info: Additional company information (optional)
        
        Returns:
            str: Customized cover letter
        """
        prompt = f"""
Customize this cover letter for {company_name}:

**Base Cover Letter:**
{base_cover_letter}

**Company:** {company_name}
{f"**Company Info:** {company_info}" if company_info else ""}

**Instructions:**
1. Replace any generic company references with {company_name}
2. If company info is provided, add a sentence showing knowledge about the company
3. Keep the same overall structure and qualifications
4. Make it feel personalized for this specific company
5. Maintain professional tone

Provide the complete customized cover letter:
"""
        
        try:
            system_prompt = "You are an expert at personalizing cover letters for specific companies."
            
            customized_letter = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500
            )
            
            return customized_letter
            
        except Exception as e:
            print(f"Error customizing cover letter: {e}")
            return None


# Example usage
if __name__ == "__main__":
    generator = AICoverLetterGenerator()
    
    sample_resume = """
    Jane Smith - Data Scientist
    
    EXPERIENCE:
    - Led machine learning projects resulting in 25% efficiency improvement
    - Developed predictive models using Python and TensorFlow
    - Collaborated with stakeholders to define business requirements
    
    SKILLS:
    Python, Machine Learning, TensorFlow, SQL, Data Visualization
    """
    
    sample_job_desc = """
    We're seeking a Data Scientist to join our team. You'll build ML models,
    analyze large datasets, and drive data-driven decision making. 
    Requirements: Python, ML experience, strong communication skills.
    """
    
    print("Testing Cover Letter Generator...")
    cover_letter = generator.generate_cover_letter(
        sample_resume,
        "Data Scientist",
        sample_job_desc,
        "Tech Corp",
        "Jane Smith",
        "jane@email.com",
        "555-0123"
    )
    
    if cover_letter:
        print("\nGenerated Cover Letter:")
        print(cover_letter)

