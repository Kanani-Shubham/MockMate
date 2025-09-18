# model.py
import requests
import os
from groq import Groq

# Get API key from environment or use default
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = "llama-3.3-70b-versatile"  # Replace with a supported model

def generate_questions(role, position, extra, num_questions):
    """
    Sends prompt to Groq API to generate interview questions.
    
    Args:
        role (str): Job role (e.g. "Python Developer")
        position (str): Position type (e.g. "Backend")
        extra (str): Additional context/requirements
        num_questions (int): Number of questions to generate
        
    Returns:
        list: Generated interview questions
    """
    prompt = (
        f"Generate {num_questions} high-quality, unique interview questions for a candidate applying "
        f"for the role of {role}, position: {position}. "
        f"Additional context: {extra}. Return only a numbered list of questions."
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
        )
        result = chat_completion.choices[0].message.content
        questions = [q.strip() for q in result.split('\n') if q.strip()]
        return questions
    except Exception as e:
        raise Exception(f"Failed to generate questions: {str(e)}")


def evaluate_answers(meta, answers):
    """
    Evaluates the interview answers and provides feedback.
    
    Args:
        meta (dict): Contains role, position and other metadata
        answers (list): List of dictionaries with question-answer pairs
    
    Returns:
        dict: Evaluation results containing raw evaluation text
    """
    role = meta.get('role', '')
    position = meta.get('position', '')
    qa_text = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in answers])

    # Changed prompt: speak directly to the candidate and use exact headings the validator expects
    prompt = f"""
You are an expert interview evaluator. Address the candidate directly using "you" (do NOT use third-person).
Evaluate these interview answers for a {meta.get('role','')} {meta.get('position','')} position.

Interview Responses:
{qa_text}

Provide the evaluation EXACTLY in this format (use "you" in each item and keep headings verbatim):

Overall Score: [score]/100

Key Strengths:
1. You [specific strength and brief example]
2. You [specific strength and brief example]
3. You [specific strength and brief example]

Key Weaknesses:
1. You [specific weakness and context]
2. You [specific weakness and context]
3. You [specific weakness and context]

Tips for Improvement:
1. You should [actionable tip]
2. You should [actionable tip]
3. You should [actionable tip]

Brief Feedback:
- Q1: You [direct short feedback referencing the candidate's answer]
- Q2: You [direct short feedback referencing the candidate's answer]
- Q3: You [direct short feedback referencing the candidate's answer]
... (one line per question)

Do not add any other text, preface, or trailing commentary. Keep headings and numbering exactly as above.
"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interview evaluator. Always provide evaluations in the exact format requested."
                },
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.7,  # Added for more consistent formatting
            max_tokens=2000   # Increased for fuller responses
        )
        result = chat_completion.choices[0].message.content
        
        # Ensure the response contains all required sections
        if not all(section in result for section in ["Overall Score:", "Key Strengths:", "Key Weaknesses:", "Tips for Improvement:"]):
            raise Exception("Evaluation response missing required sections")
            
        return {"raw_evaluation": result}
    except Exception as e:
        raise Exception(f"Failed to evaluate answers: {str(e)}")


# For testing purposes
if __name__ == "__main__":
    output = generate_questions(
        "Python Developer",
        "Backend",
        "Focus on APIs and database handling",
        5
    )
    print(output)
