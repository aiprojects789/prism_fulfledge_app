import json
import re
import streamlit as st
from collections import defaultdict
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# Helper: extract JSON array from LLM output
def extract_json_array(s: str) -> str:
    pattern = r'\[\s*(?:\{.*?\}\s*,?\s*)+\]'
    match = re.search(pattern, s, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")
    return match.group(0)

# Helper: get concept paths
def get_concept_paths(data: dict, parent_key: str = '', sep: str = '.') -> List[str]:
    paths: List[str] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            if 'description' in value or 'values' in value or 'value' in value:
                paths.append(new_key)
            else:
                for child_key, child_val in value.items():
                    if isinstance(child_val, dict):
                        paths.extend(get_concept_paths({child_key: child_val}, new_key, sep))
    return paths

# Helper: get description

def get_description_for_path(root: dict, dotted_path: str) -> str:
    parts = dotted_path.split('.') if dotted_path else []
    node = root
    for key in parts:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    return node.get('description', '') if isinstance(node, dict) else ''

# Generate a conversational question
def generate_single_question(field_path: str, intent_desc: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly AI assistant helping users build their personalized digital twin for better recommendations. Your tone should be warm, encouraging, and respectful."),
        ("user", f"""
You will be given a field from a JSON schema and a description explaining its intent.

Generate a conversational, open-ended question that:
- Feels like part of a friendly dialogue
- Offers light guidance or an example to help the user answer
- Is inclusive and privacy-aware (especially if the topic is sensitive)
- Does NOT include multiple-choice options or lists
- Sounds like something a thoughtful assistant would naturally ask

Use the field name and description to craft the question.

Example input:
Field Name: userContextAndLifestyle.lifeStageNotes  
Description: Capture the user’s current phase in life, such as studying, working, married, retired, etc.

Example output:
What stage of life are you currently in? Feel free to share if you’re studying, working, raising a family, or going through any major change right now.

Now generate a similar conversational question for:

Field Name: {field_path}  
Description: {intent_desc}
"""),
    ])
    model = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=st.secrets["api"]["key"])
    chain = prompt | model
    return chain.invoke({"field_path": field_path, "intent_desc": intent_desc}).content.strip()

# Rank & tier questions using GPT-4o
def rank_and_tier_with_gpt4o(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    system = SystemMessagePromptTemplate.from_template(
        "You are an expert in personalization and recommendation logic. "
        "Score each question (with 'field' and 'question') 0–100 on impact, rank, and bucket into three equal tiers."
    )
    human = HumanMessagePromptTemplate.from_template(
        """Here is a JSON array of questions.
Respond with ONLY a JSON array of the same objects, each with added:
- impactScore: integer 0–100
- tier: "Tier 1", "Tier 2", or "Tier 3"

Sort by descending impactScore.

```json
{questions}
```"""
    )
    prompt = ChatPromptTemplate.from_messages([system, human])
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=st.secrets["api"]["key"])
    raw = llm(prompt.format_messages(questions=json.dumps(questions, indent=2)))
    json_text = extract_json_array(raw.content)
    return json.loads(json_text)

# Enrich ranked questions with extra metadata
def enrich_questions(
    flat_questions: List[Dict[str, Any]],
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for q in flat_questions:
        full = q["field"]  
        section, *rest = full.split('.', 1)
        subsection = rest[0] if rest else ''
        description = get_description_for_path(
            schema.get(section, {}),
            subsection
        )
        enriched.append({
            "section": section,
            "subsection": subsection,
            "field": full,
            "description": description,
            "question": q["question"],
            "impactScore": q["impactScore"],
            "tier": q["tier"],
            "qest": "pending"
        })
    return enriched

# Wrap enriched questions into tier1/tier2/tier3

def wrap_questions_by_tier(
    flat_questions: List[Dict[str, Any]],
    status: str = "in_process"
) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for q in flat_questions:
        grouped[q["tier"]].append(q)

    return {
        "tier1": {"status": status, "questions": grouped.get("Tier 1", [])},
        "tier2": {"status": status, "questions": grouped.get("Tier 2", [])},
        "tier3": {"status": status, "questions": grouped.get("Tier 3", [])},
    }

# Main generation logic
def generate_questions(data: dict, section: str, category: str = None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if section == 'generalprofile':
        base = data.get('generalprofile', {})
        for p in get_concept_paths(base):
            abs_path = f"generalprofile.{p}"
            desc = get_description_for_path(base, p)
            q = generate_single_question(abs_path, desc)
            results.append({'field': abs_path, 'question': q})

    elif section == 'recommendationProfiles' and category:
        base = data.get('recommendationProfiles', {}).get(category, {})
        for p in get_concept_paths(base):
            abs_path = f"recommendationProfiles.{category}.{p}"
            desc = get_description_for_path(base, p)
            q = generate_single_question(abs_path, desc)
            results.append({'field': abs_path, 'question': q})

    elif section == 'simulationPreferences':
        base = data.get('simulationPreferences', {})
        for p in get_concept_paths(base):
            abs_path = f"simulationPreferences.{p}"
            q = generate_single_question(abs_path, '')
            results.append({'field': abs_path, 'question': q})

    return results

# Streamlit UI
st.title("📝 Digital Twin Interview Question Generator")

uploaded = st.file_uploader("Upload profile JSON", type=["json"] )
default_json: dict = {}
json_data = json.load(uploaded) if uploaded else default_json

section = st.radio(
    "Select section:",
    ("General Profile", "Recommendation Profile", "Simulation Preferences")
)

# Handler for all three branches, differing only by arguments
if section == 'General Profile' and st.button("Generate Questions"):
    with st.spinner("Generating questions..."):
        flat = generate_questions(json_data, 'generalprofile')
        ranked = rank_and_tier_with_gpt4o(flat)
        enriched = enrich_questions(ranked, json_data)
        wrapped  = wrap_questions_by_tier(enriched)

    st.json(wrapped)
    st.download_button(
        "Download Tiered Questions",
        data=json.dumps(wrapped, indent=2),
        file_name="general_tiered_questions.json"
    )

elif section == 'Recommendation Profile':
    cats = list(json_data.get('recommendationProfiles', {}).keys())
    sel  = st.selectbox("Category", cats)

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            flat     = generate_questions(json_data, 'recommendationProfiles', sel)
            ranked   = rank_and_tier_with_gpt4o(flat)
            enriched = enrich_questions(ranked, json_data)
            wrapped  = wrap_questions_by_tier(enriched)

        st.json(wrapped)
        st.download_button(
            "Download Tiered Questions",
            data=json.dumps(wrapped, indent=2),
            file_name=f"{sel}_tiered_questions.json"
        )

elif section == 'Simulation Preferences' and st.button("Generate Questions"):
    with st.spinner("Generating questions..."):
        flat     = generate_questions(json_data, 'simulationPreferences')
        ranked   = rank_and_tier_with_gpt4o(flat)
        enriched = enrich_questions(ranked, json_data)
        wrapped  = wrap_questions_by_tier(enriched)

    st.json(wrapped)
    st.download_button(
        "Download Tiered Questions",
        data=json.dumps(wrapped, indent=2),
        file_name="simulation_tiered_questions.json"
    )
