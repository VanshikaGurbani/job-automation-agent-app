"""
Job Matcher
Uses AI to calculate job match ratings and provide detailed analysis
"""
from llm_client import LLMClient
import config
from utils import calculate_keyword_match
import json


class JobMatcher:
    def __init__(self):
        """Initialize the Job Matcher"""
        self.llm = LLMClient()
    
    def calculate_match_score(self, resume_text, job_title, job_description):
        """
        Calculate comprehensive match score between resume and job
        
        Args:
            resume_text: Resume content
            job_title: Job title
            job_description: Job description
        
        Returns:
            dict: Match score and detailed analysis
        """
        # Get AI analysis
        ai_analysis = self._get_ai_match_analysis(resume_text, job_title, job_description)
        
        # Get keyword match (as a backup/supplementary score)
        keyword_score = calculate_keyword_match(resume_text, job_description)
        
        # Combine the results
        if ai_analysis:
            return {
                'overall_score': ai_analysis.get('score', keyword_score),
                'match_level': self._get_match_level(ai_analysis.get('score', keyword_score)),
                'strengths': ai_analysis.get('strengths', []),
                'gaps': ai_analysis.get('gaps', []),
                'recommendations': ai_analysis.get('recommendations', []),
                'keyword_match': keyword_score,
                'summary': ai_analysis.get('summary', '')
            }
        else:
            # Fallback to keyword-based scoring
            return {
                'overall_score': keyword_score,
                'match_level': self._get_match_level(keyword_score),
                'strengths': ['Keyword analysis completed'],
                'gaps': ['Detailed analysis unavailable'],
                'recommendations': ['Ensure your resume includes keywords from the job description'],
                'keyword_match': keyword_score,
                'summary': f'Basic keyword match score: {keyword_score}%'
            }
    
    def _get_ai_match_analysis(self, resume_text, job_title, job_description):
        """Get detailed match analysis from AI"""
        prompt = f"""
Analyze this candidate's fit for the {job_title} role and provide a match score (0-100).

**Candidate Resume:**
{resume_text}

**Job Title:** {job_title}

**Job Description:**
{job_description}

Output ONLY valid JSON (no markdown):
{{
    "score": 85,
    "summary": "2-3 sentence assessment",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "gaps": ["gap 1", "gap 2"],
    "recommendations": ["rec 1", "rec 2"]
}}
"""
        
        try:
            # Full context for accurate analysis
            result_text = self.llm.generate(
                prompt,
                system_prompt="You are an expert HR recruiter. Analyze candidate fit and output valid JSON only.",
                temperature=0.4,
                max_tokens=8192  # MAXIMUM for Gemini 2.5 Flash
            )
            
            # Try to parse JSON
            # Remove markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(result_text)
            return analysis
            
        except Exception as e:
            print(f"Error getting AI match analysis: {e}")
            return None
    
    def _get_match_level(self, score):
        """Get match level based on score"""
        if score >= config.EXCELLENT_MATCH:
            return "Excellent Match"
        elif score >= config.GOOD_MATCH:
            return "Good Match"
        elif score >= config.FAIR_MATCH:
            return "Fair Match"
        else:
            return "Poor Match"
    
    def compare_multiple_jobs(self, resume_text, jobs_list):
        """
        Compare resume against multiple jobs and rank them
        
        Args:
            resume_text: Resume content
            jobs_list: List of job dictionaries with 'title', 'description', 'company'
        
        Returns:
            list: Jobs ranked by match score
        """
        results = []
        
        for job in jobs_list:
            print(f"Analyzing: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}...")
            
            match_result = self.calculate_match_score(
                resume_text,
                job.get('title', ''),
                job.get('description', '')
            )
            
            results.append({
                'job': job,
                'match_score': match_result['overall_score'],
                'match_level': match_result['match_level'],
                'analysis': match_result
            })
        
        # Sort by match score (descending)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results
    
    def generate_interview_prep(self, resume_text, job_title, job_description, match_analysis):
        """
        Generate interview preparation tips based on match analysis
        
        Args:
            resume_text: Resume content
            job_title: Job title
            job_description: Job description
            match_analysis: Match analysis from calculate_match_score
        
        Returns:
            dict: Interview preparation tips
        """
        prompt = f"""
Based on this job match analysis, provide interview preparation guidance.

**Job Title:** {job_title}

**Match Analysis:**
- Overall Score: {match_analysis['overall_score']}
- Strengths: {', '.join(match_analysis['strengths'])}
- Gaps: {', '.join(match_analysis['gaps'])}

**Job Description:**
{job_description[:500]}...

**Resume:**
{resume_text[:500]}...

**Instructions:**
Provide actionable interview preparation tips in the following areas:

1. **Key Topics to Study**: What specific topics should the candidate review?
2. **Questions They Might Ask**: 3-5 likely interview questions based on the job
3. **How to Address Gaps**: How to address the identified gaps in the interview
4. **Stories to Prepare**: What experiences from their resume should they be ready to discuss in detail?

Keep it practical and actionable. Format as JSON:
{{
    "topics_to_study": ["topic1", "topic2", "topic3"],
    "likely_questions": ["question1", "question2", "question3"],
    "addressing_gaps": ["tip1", "tip2"],
    "key_stories": ["story1", "story2", "story3"]
}}

Provide ONLY the JSON output:
"""
        
        try:
            system_prompt = "You are an expert interview coach who helps candidates prepare effectively for job interviews. Provide your response in JSON format."
            
            result_text = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=800
            )
            
            # Parse JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            prep_tips = json.loads(result_text)
            return prep_tips
            
        except Exception as e:
            print(f"Error generating interview prep: {e}")
            return None


# Example usage
if __name__ == "__main__":
    matcher = JobMatcher()
    
    sample_resume = """
    Alex Johnson - Full Stack Developer
    
    EXPERIENCE:
    - Built responsive web applications using React and Node.js
    - Designed RESTful APIs and microservices
    - Worked with MongoDB and PostgreSQL databases
    - Implemented CI/CD pipelines using Jenkins
    
    SKILLS:
    JavaScript, React, Node.js, Python, SQL, Git, Docker
    
    EDUCATION:
    BS in Computer Science
    """
    
    sample_job_desc = """
    Senior Full Stack Developer position. We need someone with:
    - 5+ years experience with React and Node.js
    - Strong understanding of microservices architecture
    - Experience with AWS and cloud deployment
    - Database design experience (SQL and NoSQL)
    - Team leadership experience preferred
    """
    
    print("Testing Job Matcher...")
    result = matcher.calculate_match_score(sample_resume, "Senior Full Stack Developer", sample_job_desc)
    
    if result:
        print(f"\n{'='*50}")
        print(f"Match Score: {result['overall_score']}/100")
        print(f"Match Level: {result['match_level']}")
        print(f"\nSummary: {result['summary']}")
        print(f"\nStrengths:")
        for strength in result['strengths']:
            print(f"  ✓ {strength}")
        print(f"\nGaps:")
        for gap in result['gaps']:
            print(f"  ✗ {gap}")
        print(f"\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  → {rec}")

