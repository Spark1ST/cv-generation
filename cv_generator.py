from crewai import Agent, Task, Crew, LLM
import os
import json
import uuid
from dotenv import load_dotenv
import agentops

# ---------------------------
# Environment
# ---------------------------
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, "config", "key.env")
OUTPUT_ROOT = os.path.join(BASE_DIR, "printed-cv")

os.makedirs(OUTPUT_ROOT, exist_ok=True)
load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY)

# ---------------------------
# LLM
# ---------------------------
llm = LLM(
    api_key=GROQ_API_KEY,
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2
)

# ---------------------------
# Agents
# ---------------------------
def create_agents():
    return (
        Agent(
            role="CV Data Specialist",
            goal="Extract and structure professional information",
            backstory="Expert in analyzing and organizing career data",
            llm=llm,
            verbose=False
        ),
        Agent(
            role="Document Formatting Expert",
            goal="Create ATS-friendly CVs",
            backstory="Specialist in professional CV formatting",
            llm=llm,
            verbose=False
        ),
        Agent(
            role="Quality Assurance Editor",
            goal="Ensure CV meets professional standards",
            backstory="HR editor with strong editorial skills",
            llm=llm,
            verbose=False
        ),
        Agent(
            role="Career Match Analyst",
            goal="Evaluate CV against target role",
            backstory="Senior talent acquisition specialist",
            llm=llm,
            verbose=False
        ),
    )

# ---------------------------
# Tasks
# ---------------------------
def create_tasks(user_data, job_description, agents, run_dir):
    researcher, formatter, reviewer, evaluator = agents

    structured_path = os.path.join(run_dir, "structured.json")
    cv_path = os.path.join(run_dir, "cv.md")
    eval_path = os.path.join(run_dir, "evaluation.md")

    return [
        Task(
            description=f"""
Analyze and structure this raw data into clean JSON:
{json.dumps(user_data, indent=2)}
""",
            agent=researcher,
            expected_output="Structured professional data in JSON",
            output_file=structured_path,
        ),
        Task(
            description="""
Convert structured data into ATS-friendly markdown CV.
Use clear sections and concise bullet points.
""",
            agent=formatter,
            expected_output="Professional CV in markdown",
            output_file=cv_path,
        ),
        Task(
            description="""
Review and polish the CV:
- Fix grammar
- Ensure professional tone
- Maintain consistency
""",
            agent=reviewer,
            expected_output="Final polished CV markdown",
            output_file=cv_path,
        ),
        Task(
            description=f"""
Evaluate CV against job description:

{job_description}

Output ONLY the following markdown:

## Career Match Evaluation
- **Overall Score**: <score>/100
- **Experience Relevance**: <score>/20 – feedback
- **Skill Match**: <score>/20 – feedback
- **Education Suitability**: <score>/20 – feedback
- **Formatting Quality**: <score>/20 – feedback
- **Professional Tone**: <score>/20 – feedback
""",
            agent=evaluator,
            expected_output="Evaluation markdown",
            output_file=eval_path,
        ),
    ], cv_path, eval_path

# ---------------------------
# Public API
# ---------------------------
def generate_cv_and_evaluation(user_data: dict, job_description: str):
    """
    Runs CrewAI once and returns (cv_markdown, evaluation_markdown).
    Does NOT write to shared files.
    """

    run_id = str(uuid.uuid4())
    run_dir = os.path.join(OUTPUT_ROOT, run_id)
    os.makedirs(run_dir, exist_ok=True)

    agents = create_agents()
    tasks, cv_path, eval_path = create_tasks(
        user_data, job_description, agents, run_dir
    )

    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        sequential=True,
        verbose=False,
    )

    crew.kickoff()

    def read(path):
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() or None

    return read(cv_path), read(eval_path)
