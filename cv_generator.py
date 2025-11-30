# cv_generation.py

from crewai import Agent, Task, Crew, LLM
import os
import json
from dotenv import load_dotenv
import agentops
import streamlit as st

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'config', 'key.env')
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY)

# Initialize LLM
llm = LLM(
    api_key=GROQ_API_KEY,
    model="groq/llama-3.3-70b-versatile"
)

def create_agents():
    # Initialize and return agents
    researcher = Agent(
        role='CV Data Specialist',
        goal='Extract and structure professional information',
        backstory="Expert in analyzing and organizing career-related data",
        llm=llm,
        verbose=True
    )

    formatter = Agent(
        role='Document Formatting Expert',
        goal='Create professionally formatted CVs',
        backstory="Specialist in ATS-friendly formatting and visual presentation",
        llm=llm,
        verbose=True
    )

    reviewer = Agent(
        role='Quality Assurance Editor',
        goal='Ensure CV meets professional standards',
        backstory="Experienced HR professional with strong editorial skills",
        llm=llm,
        verbose=True
    )

    suitability_checker = Agent(
        role='Career Match Analyst',
        goal='Evaluate CV against target position',
        backstory="Talent acquisition specialist with 10+ years experience",
        llm=llm,
        verbose=True
    )

    return researcher, formatter, reviewer, suitability_checker

def create_tasks(user_data, job_description, researcher, formatter, reviewer, suitability_checker):
    # Create tasks based on the user input and job description
    research_task = Task(
        description=f"""Analyze and structure this raw data:
        {json.dumps(user_data)}
        Create comprehensive CV sections with proper categorization""",
        agent=researcher,
        expected_output="Structured JSON with categorized professional information",
        output_file='printed-cv/'+'structured_data.json'
    )

    format_task = Task(
        description="""Convert structured data into ATS-friendly markdown format.
        Use professional templates and ensure proper section ordering:
        1. Summary
        2. Experience
        3. Education
        4. Skills
        5. Certifications""",
        agent=formatter,
        expected_output="Well-formatted CV in markdown with consistent styling",
        output_file='printed-cv/'+'formatted_cv.md'
    )

    review_task = Task(
        description="""Verify CV quality:
        - Check for grammatical errors
        - Ensure consistent tense usage
        - Validate chronological order
        - Confirm professional tone""",
        agent=reviewer,
        expected_output="Polished CV meeting all professional guidelines",
        output_file='printed-cv/'+'reviewed_cv.md'
    )

    evaluation_task = Task(
        description=f"""Evaluate the generated CV against the job description:
{job_description}

Use the following markdown template for output:

## Career Match Evaluation
- **Overall Score**: <score>/100
- **Experience Relevance**: <score>/20 – feedback
- **Skill Match**: <score>/20 – feedback
- **Education Suitability**: <score>/20 – feedback
- **Formatting Quality**: <score>/20 – feedback
- **Professional Tone**: <score>/20 – feedback

Provide concise, clear feedback inline.""",
        agent=suitability_checker,
        expected_output="Markdown with scores and detailed feedback",
        output_file='printed-cv/'+'evaluation.md'
    )

    return research_task, format_task, review_task, evaluation_task

def generate_cv_and_evaluation(user_data, job_description):
    """
    Run the full CrewAI workflow and return the generated CV and evaluation markdown.
    """
    # Instantiate agents & tasks
    researcher, formatter, reviewer, suitability_checker = create_agents()
    tasks = create_tasks(user_data, job_description, researcher, formatter, reviewer, suitability_checker)

    # Execute workflow\    
    crew = Crew(
        agents=[researcher, formatter, reviewer, suitability_checker],
        tasks=tasks,
        verbose=True,
        sequential=True
    )
    crew.kickoff()

    # Read outputs
    cv_md = ""
    eval_md = ""
    try:
        with open('printed-cv/'+'formatted_cv.md', 'r', encoding='utf-8') as f:
            cv_md = f.read()
    except FileNotFoundError:
        cv_md = None

    try:
        with open('printed-cv/'+'evaluation.md', 'r', encoding='utf-8') as f:
            eval_md = f.read()
    except FileNotFoundError:
        eval_md = None

    return cv_md, eval_md


def read_file_or_warn(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                st.warning(f"⚠️ File {path} is empty.")
                return None
            return content
    except FileNotFoundError:
        st.error(f"❌ File not found: {path}")
        return None