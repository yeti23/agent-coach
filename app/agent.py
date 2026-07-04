# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Personal Coach — ADK 2.0 graph workflow agent.

Workflow:
  START
    └─► classifier (LLM) — classifies query as "general" or "health"
          ├─► (route="general") general_knowledge_agent (LLM)
          └─► (route="health")  health_agent (LLM)
                └─► (both converge) final_output — emits content to UI
"""

import os

import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.workflow import Workflow
from google.genai import types
from mcp import StdioServerParameters
from pydantic import BaseModel

from app.tools import get_exercise_activities, get_resting_health_summary

import pathlib
from google.adk.skills import load_skill_from_dir
# Resolve the path to your custom skill directory
SKILL_DIR = pathlib.Path(__file__).parent / "skills"
# Load the skill (it automatically reads SKILL.md and parses any assets/references)
user_summary_skill = load_skill_from_dir(SKILL_DIR / "user-summary")
activity_skill = load_skill_from_dir(SKILL_DIR / "exercise-week")

from google.adk.tools import skill_toolset
# Group your loaded skills under a SkillToolset
skills_toolset = skill_toolset.SkillToolset(
    skills=[user_summary_skill, activity_skill]
)

# ---------------------------------------------------------------------------
# PubMed MCP toolset connection
# ---------------------------------------------------------------------------
pubmed_mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=["/Users/jeanpier/Developer/GenerativeAI/Kaglle5dgai_Vibe_Coding/pubmed-mcp-server/dist/index.js"],
            env={"MCP_TRANSPORT_TYPE": "stdio"},
        ),
        timeout=15.0,
    )
)

# ---------------------------------------------------------------------------
# GCP / Vertex AI environment
# ---------------------------------------------------------------------------
#try:
#    _, _project_id = google.auth.default()
#    os.environ["GOOGLE_CLOUD_PROJECT"] = _project_id
#except Exception:  # DefaultCredentialsError or similar — credentials not configured yet
#    pass
#os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
#os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------
_MODEL = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3),
)

# ---------------------------------------------------------------------------
# Step 1 — Classifier
# ---------------------------------------------------------------------------


class ClassifierOutput(BaseModel):
    """Structured output from the classifier node."""

    category: str  # "general", "health", or "unrelated"
    reasoning: str


classifier_agent = LlmAgent(
    name="classifier",
    model=_MODEL,
    instruction=(
        "You are a query classifier for a personal coach assistant.\n\n"
        "Your task is to read the user's query and decide whether it is:\n"
        '- "general": a general knowledge question, scientific topics, or queries '
        "requesting research papers, publications, literature databases, or articles "
        "(e.g. searching PubMed or Europe PMC for biomedical studies).\n"
        '- "health": a question related to personal health, fitness, wellness, '
        "nutrition, exercise tracking (e.g. daily steps, heart rate, sleep metrics, "
        "personal workout summaries, weight/height).\n"
        '- "unrelated": a query completely unrelated to biomedical/life science '
        "literature or personal health, wellness, fitness, or medicine (e.g. asking "
        "about movie reviews, general programming/coding, business, politics, "
        "writing fiction, general chit-chat, etc.).\n\n"
        "Always respond with the appropriate category and a brief reasoning "
        "explaining why you classified the query that way.\n\n"
        "When in doubt, prefer 'general'."
    ),
    output_schema=ClassifierOutput,
    output_key="classification",
)


# ---------------------------------------------------------------------------
# Routing node — reads classifier output and emits a route signal
# ---------------------------------------------------------------------------


def route_query(node_input: dict) -> Event:
    """Emit a routing event based on the classifier's category.

    classifier_agent has output_schema=ClassifierOutput, so ADK emits a dict
    to downstream function nodes (not a Pydantic instance).
    """
    classification = ClassifierOutput(**node_input)
    category = (classification.category or "general").strip().lower()
    
    if category == "unrelated":
        route = "unrelated"
    elif category == "health":
        route = "health"
    else:
        route = "general"
        
    return Event(output=node_input, route=route)


# ---------------------------------------------------------------------------
# Out of Scope / Unrelated decline node
# ---------------------------------------------------------------------------


def decline_unrelated(node_input: dict) -> dict:
    """Politely decline to answer unrelated queries.

    Returns a dict conforming to AgentAnswer.
    """
    return {
        "answer": (
            "I apologize, but as your personal coach, I can only assist you "
            "with biomedical or life science queries, or personal health and fitness questions. "
            "Please let me know if you have a question in those areas!"
        ),
        "topic_area": "Out of Scope",
    }


# ---------------------------------------------------------------------------
# Step 2a — General Knowledge Agent
# Step 2a — General/PubMed Knowledge Agent
# ---------------------------------------------------------------------------


class AgentAnswer(BaseModel):
    """Final answer from a specialist agent."""

    answer: str
    topic_area: str


pubmed_researcher = LlmAgent(
    name="pubmed_researcher",
    model=_MODEL,
    instruction=(
        "You are an expert biomedical and life science literature research assistant.\n\n"
        "Your task is to answer the user's question or find resources using the PubMed MCP tools. "
        "Use the search, fetch, and format tools to locate and present accurate research papers, "
        "abstracts, and citations from PubMed or Europe PMC.\n\n"
        "Always try to find real, relevant scientific publications. Summarize key findings "
        "and list the relevant PMIDs, PMCIDs, or DOIs."
    ),
    tools=[pubmed_mcp_toolset],
)

pubmed_formatter = LlmAgent(
    name="pubmed_formatter",
    model=_MODEL,
    instruction=(
        "You are a response formatter for a biomedical literature research coach.\n\n"
        "Given the research findings provided in the input, construct a structured response.\n"
        "Format a clear, engaging, and professional response summarizing the findings and citing "
        "specific papers/PMIDs.\n\n"
        "Set topic_area to a short label describing the scientific field (e.g. "
        "'Genetics', 'Virology', 'Oncology', 'Cardiology', 'Immunology')."
    ),
    output_schema=AgentAnswer,
    output_key="agent_answer",
)

# ---------------------------------------------------------------------------
# Step 2b — Health Agent (Split into tool-using researcher and formatter)
# ---------------------------------------------------------------------------

health_researcher = LlmAgent(
    name="health_researcher",
    model=_MODEL,
    instruction=(
        "You are an expert health and wellness coach with access to the user's "
        "personal daily health metrics and workout history.\n\n"
        "Your task is to answer the user's question by fetching their actual personal data "
        "using the resting health summary and exercise activities tools.\n\n"
        "Use the tools when the query involves sleep, steps, heart rate, weight, height, "
        "or specific workout sessions (e.g. bike rides, muscle building).\n\n"
        "Synthesize this personal data with evidence-based health coaching to provide "
        "personalized, helpful recommendations."
    ),
    tools=[get_resting_health_summary, get_exercise_activities, skills_toolset],
)

health_formatter = LlmAgent(
    name="health_formatter",
    model=_MODEL,
    instruction=(
        "You are a response formatter for a personalized health and wellness coach.\n\n"
        "Given the personal health findings in the input, construct a structured response.\n"
        "Format a clear, engaging, and personalized coaching response. Incorporate the "
        "actual numbers retrieved (steps, sleep time, average heart rate, etc.) and relate "
        "them to the user's inquiry.\n\n"
        "IMPORTANT: You are not a licensed medical professional. Always recommend consulting "
        "a qualified healthcare provider for personal medical decisions or emergencies. "
        "Never diagnose conditions.\n\n"
        "Set topic_area to a short label such as 'Nutrition', 'Fitness', 'Mental Health', "
        "'Preventive Care', 'General Wellness', etc."
    ),
    output_schema=AgentAnswer,
    output_key="agent_answer",
)

health_agent = health_researcher

# ---------------------------------------------------------------------------
# Step 3 — Final output node (renders visible content in the web UI)
# ---------------------------------------------------------------------------


def final_output(node_input: dict):
    """Emit a user-visible content event and pass output downstream.

    LlmAgent with output_schema emits a dict (not a Pydantic instance)
    when passing output to downstream function nodes.
    """
    # Reconstruct typed access from the dict emitted by the LlmAgent
    answer_obj = AgentAnswer(**node_input)
    response_text = answer_obj.answer
    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=response_text)],
        )
    )
    yield Event(output=response_text)


# ---------------------------------------------------------------------------
# Workflow graph
# ---------------------------------------------------------------------------

root_agent = Workflow(
    name="personal_coach",
    description=(
        "A personal coach that classifies your query and routes it to "
        "the right specialist: general knowledge or health & wellness."
    ),
    edges=[
        # Step 1: classify the incoming query
        ("START", classifier_agent),
        # Step 2: route to the right specialist via routing-map dict syntax:
        #   {route_value: target_node, ...}
        (classifier_agent, route_query),
        (route_query, {
            "general": pubmed_researcher,
            "health": health_researcher,
            "unrelated": decline_unrelated
        }),
        # Step 3: general/biomedical branch runs researcher then formatter
        (pubmed_researcher, pubmed_formatter),
        # Step 4: health branch runs researcher then formatter
        (health_researcher, health_formatter),
        # Step 5: both branches converge at final_output
        (pubmed_formatter, final_output),
        (health_formatter, final_output),
        # Unrelated/decline branch goes directly to final_output
        (decline_unrelated, final_output),
    ],
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = App(
    root_agent=root_agent,
    name="app",
)
