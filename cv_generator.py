from crewai import Agent, Task, Crew, LLM
import os
import json
import hashlib
from dotenv import load_dotenv

# -------------------------------
# Environment Setup
# -------------------------------
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, "config", "key.env")
OUTPUT_DIR = os.path.join(BASE_DIR, "printed-cv")

os.makedirs(OUTPUT_DIR, exist_ok=True)
load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -------------------------------
# LLM (Groq)
# -------------------------------
llm = LLM(
    api_key=GROQ_API_KEY,
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2
)

# -------------------------------
# Utilities
# -------------------------------
def _hash_payload(user_data: dict, job_description: str) -> str:
    raw = json.dumps(
        {"user_data": user_data, "job_description": job_description},
        sort_keys=True
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_file(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return content if content else None


# -------------------------------
# Agents
# -------------------------------
def create_agents():
    return (
        Agent(
            role="CV Data Specialist",
            goal="Ensure CV data is structured and consistent",
            backstory="Expert in CV data normalization",
            llm=llm
        ),
        Agent(
            role="CV Formatter",
            goal="Generate a grounded ATS-friendly CV",
            backstory="Professional resume writer",
            llm=llm
        ),
        Agent(
            role="CV Reviewer",
            goal="Polish CV without changing facts",
            backstory="HR editor",
            llm=llm
        ),
        Agent(
            role="Career Match Analyst",
            goal="Evaluate CV against job description",
            backstory="Senior recruiter",
            llm=llm
        ),
    )


# -------------------------------
# Tasks (ONE VERSION ONLY)
# -------------------------------
def create_tasks(user_data, job_description, agents):
    researcher, formatter, reviewer, evaluator = agents

    cv_path = os.path.join(OUTPUT_DIR, "reviewed_cv.md")
    eval_path = os.path.join(OUTPUT_DIR, "evaluation.md")

    grounded_input = json.dumps(user_data, indent=2)
# eno wlahy da goz2 mas2ol 3ala tzbet el cv be est3mal el ai 
    research_task = Task(
        description=f"""
Normalize user CV data WITHOUT adding information.

User data:
{grounded_input}
""",
        agent=researcher,
        expected_output="Normalized CV data"
    )

    format_task = Task(
        description=f"""
Generate a COMPLETE Markdown CV using ONLY the data below.
DO NOT invent content.
DO NOT leave sections empty if data exists.

User data:
{grounded_input}

Rules:
- Experience section must contain the experience text
- Education section must contain the education text
- Skills must be listed if provided
- Use Markdown headings (#, ##)
""",
        agent=formatter,
        expected_output="Complete grounded Markdown CV",
        output_file=cv_path
    )

    review_task = Task(
        description=f"""
Review the CV for grammar and formatting ONLY.
DO NOT rewrite or overwrite content.

User data:
{grounded_input}
""",
        agent=reviewer,
        expected_output="Review notes only"
    )

    evaluation_task = Task(
        description=f"""
Evaluate the CV against the job description.

Job description:
{job_description}

User data:
{grounded_input}

Output ONLY markdown:

## Career Match Evaluation
- **Overall Score**: <score>/100
- **Experience Relevance**: <score>/20 – feedback
- **Skill Match**: <score>/20 – feedback
- **Education Suitability**: <score>/20 – feedback
- **Formatting Quality**: <score>/20 – feedback
- **Professional Tone**: <score>/20 – feedback
""",
        agent=evaluator,
        expected_output="Markdown evaluation",
        output_file=eval_path
    )

    return [research_task, format_task, review_task, evaluation_task], cv_path, eval_path




# -------------------------------
# Public API
# -------------------------------
def generate_cv_and_evaluation(user_data: dict, job_description: str):
    run_id = _hash_payload(user_data, job_description)

    cv_path = os.path.join(OUTPUT_DIR, "reviewed_cv.md")
    eval_path = os.path.join(OUTPUT_DIR, "evaluation.md")

    cached_cv = _read_file(cv_path)
    cached_eval = _read_file(eval_path)

    if cached_cv and cached_eval:
        return cached_cv, cached_eval

    agents = create_agents()
    tasks, _, _ = create_tasks(user_data, job_description, agents)

    Crew(
        agents=list(agents),
        tasks=tasks,
        sequential=True,
        verbose=False
    ).kickoff()

    return _read_file(cv_path), _read_file(eval_path)
