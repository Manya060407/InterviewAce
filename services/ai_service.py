import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if (api_key and "AIzaSy" in api_key and "..." not in api_key) else None

def generate_interview_questions(job_role, difficulty, interview_type, experience, total_questions=5):
    """Generates interview questions dynamically using Gemini API or role-aware fallback."""
    total_questions = int(total_questions)
    
    if client:
        prompt = f"""
        Act as an expert interviewer for the role: '{job_role}'.
        Generate exactly {total_questions} natural, highly relevant, and distinct interview questions appropriate for this specific position.
        
        Parameters:
        - Job Role: {job_role}
        - Difficulty: {difficulty}
        - Round Type: {interview_type}
        - Experience Level: {experience}

        Important: Ensure questions use domain-appropriate language (e.g., teaching methods/curriculum for teachers, technical architecture for developers, communication/strategy for management).

        Return ONLY a raw JSON array of strings without markdown syntax.
        Example format: ["Question 1?", "Question 2?"]
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            questions = json.loads(response.text)
            if isinstance(questions, list) and len(questions) > 0:
                return questions[:total_questions]
        except Exception as e:
            print(f"\n--- GEMINI QUESTION ERROR: {e} ---\n")

    # Role-Aware Intelligent Fallback Pool
    role_lower = job_role.lower()
    
    if any(k in role_lower for k in ['teacher', 'educator', 'faculty', 'professor', 'tutor', 'instructor']):
        base_pool = [
            f"What is your approach to designing lesson plans and curriculum for a {job_role} at a {difficulty} level?",
            f"How do you handle a classroom with students who have different learning abilities and pacing?",
            f"Describe a challenging classroom situation or student engagement issue you faced as a {job_role} and how you resolved it.",
            f"What methods or digital tools do you use to evaluate student progress and keep them engaged?",
            f"How do you incorporate subject fundamentals, ethics, and interactive activities into your teaching routine?",
            f"How do you handle feedback or concerns from parents and school administration regarding student performance?",
            f"Describe your methodology for introducing complex concepts to beginners in simple, understandable terms.",
            f"How do you handle classroom management and maintain a positive learning environment?",
            f"What continuous learning or professional development activities do you pursue to improve your teaching skills?",
            f"Why do you want to work as a {job_role}, and what key qualities make an outstanding educator in this subject?"
        ]
    elif any(k in role_lower for k in ['hr', 'recruiter', 'manager', 'marketing', 'sales']):
        base_pool = [
            f"What core strategies do you use to excel as a {job_role} ({difficulty} level)?",
            f"Describe a difficult workplace dispute or challenging client situation you managed and how you handled it.",
            f"How do you measure success and track key performance metrics in your daily responsibilities as a {job_role}?",
            f"What tools and communication techniques do you use to coordinate effectively across teams?",
            f"How do you prioritize urgent tasks when handling multiple projects or candidate requests at once?",
            f"Walk us through your step-by-step workflow when taking on a new campaign or requisition as a {job_role}.",
            f"Describe a situation where you had to make a tough decision under tight deadlines.",
            f"How do you maintain compliance, professional ethics, and organizational standards in your work?",
            f"How do you stay updated with industry trends, policies, and best practices relevant to a {job_role}?",
            f"Where do you see the biggest growth opportunities for a {job_role} over the next few years?"
        ]
    else:
        # Technical / General Role Fallback
        base_pool = [
            f"What are the essential core fundamentals and tools required for a {job_role} ({difficulty} level)?",
            f"Describe a challenging problem or project you worked on as a {job_role} and how you solved it.",
            f"What are the best practices for quality assurance, testing, and troubleshooting in {job_role} work?",
            f"How do you keep up with modern tools, frameworks, and industry trends relevant to a {job_role}?",
            f"How do you handle bottlenecks and edge cases when working on {interview_type} tasks?",
            f"Walk through your step-by-step methodology when starting a new {job_role} project from scratch.",
            f"What security or data standards do you follow in your daily work as a {job_role}?",
            f"How do you collaborate with cross-functional team members during a project sprint?",
            f"Describe a scenario where you had to balance quality versus delivery deadlines for a {job_role} task.",
            f"What environment setups and software tools do you prefer for high productivity as a {job_role}?"
        ]
    
    return base_pool[:total_questions]

def evaluate_interview_session(job_role, QA_pairs):
    """Evaluates candidate answers fairly using Gemini API or dynamic fallback."""
    if client:
        prompt = f"""
        Act as an experienced hiring manager evaluating a candidate for '{job_role}'.
        Review these question and answer pairs:
        {json.dumps(QA_pairs, indent=2)}

        SCORING RULES (Use full 0 to 10 scale per question):
        - 9-10/10: Exceptional, detailed, accurate, structured response tailored to {job_role}.
        - 7-8/10: Good answer covering core concepts, but missing slight depth or examples.
        - 5-6/10: Average or partial answer. Correct direction, but brief.
        - 3-4/10: Weak answer. Incomplete or vague.
        - 0-2/10: Gibberish (e.g., 'nrkrhth'), single-word lazy text ('no', 'idk'), or totally off-topic input.

        Return ONLY a JSON object:
        {{
            "overall_score": 75,
            "strengths": ["Clear communication of core domain concepts", "Good practical examples"],
            "weaknesses": ["Varying depth in some answers"],
            "suggested_topics": ["Domain Best Practices"],
            "evaluations": [
                {{
                    "question": "Question text",
                    "user_answer": "Candidate answer",
                    "score": 7,
                    "strengths": "Understood the main idea well.",
                    "weaknesses": "Could provide more specific tools or practical examples.",
                    "missing_points": "Detailed case scenario.",
                    "improved_answer": "Include concrete examples relevant to the role."
                }}
            ]
        }}
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            result = json.loads(response.text)
            if "overall_score" in result:
                return result
        except Exception as e:
            print(f"\n--- GEMINI EVALUATION ERROR: {e} ---\n")

    # Nuanced Fallback Scoring
    evals = []
    total_score = 0
    for item in QA_pairs:
        ans = item.get('answer', '').strip()
        words = len(ans.split())
        lower_ans = ans.lower()
        
        is_junk = any(x in lower_ans for x in ['nrkrhth', 'sajcijd', 'ewfrtb', 'asdf', 'qwerty']) or lower_ans in ['no', 'idk', 'na', 'none', '.']
        
        if is_junk or words < 3:
            score = 0
            strengths = "None"
            weaknesses = "Answer was invalid, gibberish, or empty."
            missing = "Complete explanation of concepts."
            improved = "Provide a meaningful, detailed response."
        elif words >= 35:
            score = 10
            strengths = "Comprehensive, clear, and well-structured answer."
            weaknesses = "None. Great domain understanding."
            missing = "Covered key aspects thoroughly."
            improved = f"Excellent response for a {job_role}!"
        elif words >= 20:
            score = 8
            strengths = "Good structured answer with clear points."
            weaknesses = "Could add slightly more specific examples."
            missing = "Specific metrics or advanced outcomes."
            improved = f"Include specific methods or examples relevant to a {job_role}."
        elif words >= 10:
            score = 6
            strengths = "Understood the basic core concept."
            weaknesses = "Answer is quite brief."
            missing = "Detailed step-by-step methodology."
            improved = "Elaborate with practical examples."
        else:
            score = 4
            strengths = "Attempted the question."
            weaknesses = "Very short response."
            missing = "Domain details and core explanation."
            improved = "Provide a full paragraph explaining your approach."
            
        total_score += score
        evals.append({
            "question": item.get('question', 'Question'),
            "user_answer": ans,
            "score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_points": missing,
            "improved_answer": improved
        })

    avg = int((total_score / (len(QA_pairs) * 10)) * 100) if QA_pairs else 0
    return {
        "overall_score": avg,
        "strengths": ["Good effort across questions"],
        "weaknesses": ["Inconsistent answer length and depth"],
        "suggested_topics": [f"{job_role} Core Knowledge"],
        "evaluations": evals
    }