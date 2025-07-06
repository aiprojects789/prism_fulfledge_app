import json
# import openai
from openai import OpenAI
import os
from duckduckgo_search import  DDGS 
from duckduckgo_search.exceptions import DuckDuckGoSearchException
# import textwrap
from itertools import islice
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st 
import time





firebase_config = st.secrets["firebase"]


# Setting up firebase
cred = credentials.Certificate(dict(firebase_config))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()



# fetching the api key 
openai_key = st.secrets["api"]["key"]

# defining function to load profile
def load_user_profile():
    """Loads and parses the user profile from Firebase"""
    doc_ref = db.collection("user_collection").document("profile_strcuture.json")
    doc = doc_ref.get()

    if doc.exists:
        print("Profile loaded from Firebase")
        return doc.to_dict()
    else:
        print("No profile found in Firebase")
        return {}



# # Searching web for getting updated results
# def search_web(query, max_results=3):
#     with DDGS() as ddgs:
#         results = islice(ddgs.text(query), max_results)
#         return list(results)




def search_web(query, max_results=3, max_retries=3, base_delay=1.0):
    """
    Query DuckDuckGo via DDGS.text(), returning up to max_results items.
    On a 202 rate‑limit, retries with exponential back‑off.
    """
    for attempt in range(1, max_retries + 1):
        try:
            with DDGS() as ddgs:
                return list(islice(ddgs.text(query), max_results))
        except DuckDuckGoSearchException as e:
            msg = str(e)
            if "202" in msg:
                wait = base_delay * (2 ** (attempt - 1))
                print(f"[search_web] Rate‑limited (202). Retry {attempt}/{max_retries} in {wait:.1f}s…")
                time.sleep(wait)
            else:
                # unexpected error, re‑raise
                raise
    # if we reach here, all retries failed
    print(f"[search_web] Failed to fetch results after {max_retries} attempts.")
    return []

# Defining function for generating recommendations
def generate_recommendations(user_profile, user_query):
    """
    Generates 3 personalized recommendations using:
    1. User profile data
    2. The specific query
    3. Fresh web search results
    """
    # Geting current web context
    search_results = search_web(f"{user_query} recommendations 2023")
    
    prompt = f"""
    **Task**: Generate exactly 3 highly personalized recommendations based on:
    
    **User Profile**:
    {json.dumps(user_profile, indent=2)}
    
    **User Query**:
    "{user_query}"
    
    **Web Context** (for reference only):
    {search_results}
    
    **Requirements**:
    1. Each recommendation must directly reference profile details
    2. Blend the user's core values and preferences
    3. Only suggest what is asked for suggest no extra advices.
    4. Format as numbered items with:
       - Title
       - Why it matches:


      **Output Example**:
    [
      {{
         "title": "Creative Project Tool",
         "reason": "Matches your love for storytelling and freelance work. Try Notion's creative templates for content planning."
      }},
      {{
         "title": "Historical Drama Series",
         "reason": "Resonates with your interest in personal struggles and leadership as shown in historical figures."
      }},
      {{
         "title": "Motivational Biopic",
         "reason": "Highlights overcoming personal difficulties aligning with your experiences of resilience."
      }}
    ]
    
    Generate your response in JSON format."""
    
    # **Output Example**:
    # 1. [Creative Project Tool] 
    #    - Why: Matches your love for storytelling and freelance work
    #    - Try: Notion's creative templates for content planning
    
    # Generate your response:
    # """

    # Setting up LLM
    client = OpenAI(api_key=openai_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a recommendation engine that creates hyper-personalized suggestions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7  
    )
    
    return response.choices[0].message.content

