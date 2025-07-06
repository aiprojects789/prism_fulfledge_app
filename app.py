import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from upload_to_db import upload_json_data_to_firestore, document_exists
import json

from interview_agent import InterviewAgent
from twin import load_user_profile, generate_recommendations
from quest_generate import get_pending_questions_by_field

# --- CONFIG & FIREBASE SETUP ---
openai_key     = st.secrets["api"]["key"]
firebase_config = st.secrets["firebase"]

cred = credentials.Certificate(dict(firebase_config))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()



# --- PAGE TITLE ---
st.markdown(
    '<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>',
    unsafe_allow_html=True
)




# --- SESSION STATE FLAGS ---
if "show_recs" not in st.session_state:
    st.session_state.show_recs = False
if "interview_messages" not in st.session_state:
    st.session_state.interview_messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo trans.png", width=200)

    # custom button styling
    st.markdown("""
    <style>
      .stButton button {
        background-color: #2c2c2e;
        color: white;
        font-size: 16px;
        padding: 8px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
      }
      .stButton button:hover { background-color: #95A5A6; }
      .stButton button:active { background-color: #BDC3C7; }
    </style>""", unsafe_allow_html=True)

    # Switch to Recommendation mode
    if st.sidebar.button("Get Recommendation"):
        st.session_state.show_recs = True

    # Reset everything
    if st.sidebar.button("Reset Interview"):
        for key in ["interview_messages", "interview_agent", "show_recs"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    
# --- MAIN PAGE CONTENT ---
st.markdown("---")

# if st.session_state.show_recs:
if "show_recs" in st.session_state and st.session_state.show_recs:
    # --------------- RECOMMENDATION UI ---------------
    st.subheader("Personalized Recommendations")

    # Load profile once
    if "profile_loaded" not in st.session_state:
        st.session_state.profile_loaded = load_user_profile()

    if not st.session_state.profile_loaded:
        st.error("No profile found—complete the interview first.")
    else:
        # ask for query
        query = st.text_input("What would you like recommendations for?", key="rec_query")
        if st.button("Generate Recommendations"):
            with st.spinner("Thinking…"):
                try:
            
                    recs_json = generate_recommendations(st.session_state.profile_loaded, query)

                    recs = json.loads(recs_json)

                    # Normalize to list
                    if isinstance(recs, dict):
                        if "recommendations" in recs and isinstance(recs["recommendations"], list):
                            recs = recs["recommendations"]
                        else:
                            recs = [recs]

                    if not isinstance(recs, list):
                        st.error("❌ Unexpected response format – expected a list of recommendations.")
                    else:
                        for i, item in enumerate(recs, 1):
                            title = item.get("title", "<no title>")
                            reason = item.get("reason", "<no reason>")
                            st.markdown(f"**{i}. {title}**")
                            st.write(reason)

                except Exception as err:
                    st.error(f"Failed: {err}")

    # “Back” button
    if st.button("← Back to Interview"):
        st.session_state.show_recs = False
        st.rerun()

else:
    # --------------- INTERVIEW UI ---------------
    st.subheader("Prism Interview Agent")
    st.write("Answer questions to build your profile:")


# --- Main Interview Setup ---
if "interview_agent" not in st.session_state:
    # Load tiered questions
    tier_doc  = db.collection("question_collection") \
                   .document("general_tiered_questions.json") \
                   .get()
    tier_data = tier_doc.to_dict()
    pending   = get_pending_questions_by_field(tier_data)

    if pending:
        qlist = [{"field": f, "question": txt} for f, txt in pending.items()]
        agent = InterviewAgent(
            openai_key, qlist,
            "user_collection", "profile_strcuture.json",
            "question_collection", "general_tiered_questions.json"
        )
        st.session_state.interview_agent = agent
        st.session_state.interview_messages = [
            {"role": "assistant", "content": "Welcome! Let's build your profile."},
            {"role": "assistant", "content": agent.get_current_question()["question"]}
        ]
    else:
        # If there are zero pending questions at startup:
        st.session_state.interview_agent = None
        st.session_state.interview_messages = [
            {"role": "assistant", "content": "✅ Profile already complete."}
        ]



agent = st.session_state.get("interview_agent")
if not agent:
    st.info("✅ Profile already complete—no interview needed.")
else:
    # 1) render history…
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])


# Callback to process a user reply
def handle_user_reply():
    user_input = st.session_state.user_input
    agent      = st.session_state.interview_agent

    # Append user message
    st.session_state.interview_messages.append({
        "role": "user", "content": user_input
    })

    # Submit to agent
    agent.submit_answer(user_input)

    # Persist updates
    try:
        db.collection("user_collection") \
          .document("profile_strcuture.json") \
          .set(agent.master_profile)
        db.collection("question_collection") \
          .document("general_tiered_questions.json") \
          .set(agent.tier_questions)
    except Exception as e:
        st.error(f"❌ Failed to save to Firestore: {e}")

    # Append next question or completion
    if agent.is_complete():
        st.session_state.interview_messages.append({
            "role": "assistant",
            "content": "✅ Interview complete! Profile saved."
        })
    else:
        next_q = agent.get_current_question()
        st.session_state.interview_messages.append({
            "role": "assistant",
            "content": next_q.get("question", "⚠️ No more questions.")
        })

# Render the chat input with the on_submit callback
st.chat_input(
    "Your answer…",
    key="user_input",
    on_submit=handle_user_reply
)
