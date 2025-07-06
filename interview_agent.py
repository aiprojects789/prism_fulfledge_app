import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import streamlit as st
from quest_generate import get_pending_questions_by_field

import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Fetching api key
api_key = st.secrets["api"]["key"]

# Firestore client
db = firestore.client()


# Defining llm
def llm_bot(api_key):
    llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=200)
    return llm


class InterviewAgent:
    # Defining main interview agent logic
    def __init__(self, api_key: str,
                 questions_list: list,
                 master_collection: str,
                 master_doc_id: str,
                 tiers_collection: str,
                 tiers_doc_id: str,):
        """
        api_key: OpenAI API key string
        questions_list: simple list of question dicts with 'field' and 'question'
        master_path: path to the master profile JSON file
        tiers_path: path to the tier questions JSON file
        """
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=200
        )
        # Single dynamic phase using provided list of question dicts
        self.phases = [
            {
                "name": "Dynamic Questions",
                "instructions": (
                    "Please answer the following questions in order. "
                    "There are no right or wrong answers."
                ),
                "questions": questions_list,
                "tier_name": "tier1"
            }
        ]
        self.conversation = []
        self.current_phase = 0
        self.current_question = 0
        self.follow_up_depth = 0


        # Firestore paths
        self.master_collection = "user_collection"
        self.master_doc_id  = "profile_strcuture.json"
        self.tiers_collection = "question_collection"
        self.tiers_doc_id = "general_tiered_questions.json"


        # Load JSON data from Firestore
        master_doc = db.collection(self.master_collection).document(self.master_doc_id).get()
        tiers_doc = db.collection(self.tiers_collection).document(self.tiers_doc_id).get()
        if not master_doc.exists or not tiers_doc.exists:
            raise ValueError("Master profile or tier questions document not found in Firestore.")

        self.master_profile = master_doc.to_dict()
        self.tier_questions = tiers_doc.to_dict()


    def set_nested(self, data: dict, dotted_path: str, value):
        """
        Given a dict `data`, walks the keys in `dotted_path` (e.g.
        "userContextAndLifestyle.userLocation.specificCity") and sets
        the final key to `value`. Creates intermediate dicts if needed.
        """
        keys = dotted_path.split('.')
        d = data
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def get_current_question(self):
        """Return the current question dict, or None if interview is finished."""
        if self.current_phase >= len(self.phases):
            return None
        phase = self.phases[self.current_phase]
        if self.current_question >= len(phase["questions"]):
            return None
        return phase["questions"][self.current_question]

    def apply_responses_to_profile(
        self,
        responses: dict,
        tier_name: str = "tier1"
    ):
        """
        Apply user responses back into the loaded master_profile and tier_questions.

        responses: dict mapping field dot-paths to the user's answers
                   e.g. {"userLocation.specificCity": "Karachi", ...}
        tier_name: which tier to operate on (default "tier1")
        """
        questions = self.tier_questions.get(tier_name, {}).get("questions", [])
        for q in questions:
            field = q.get("field")
            if q.get("qest") == "pending" and field in responses:
                # update nested master profile
                self.set_nested(
                    self.master_profile["generalprofile"],
                    field,
                    responses[field]
                )
                # mark question answered
                q["qest"] = "answered"

    def is_complete(self):
        """Return True if all phases & questions have been answered."""
        # Finished current phase?
        if self.current_phase < len(self.phases):
            phase = self.phases[self.current_phase]
            if self.current_question < len(phase["questions"]):
                return False
        # Check if any further phases remain
        return self.current_phase >= len(self.phases) - 1 and \
               self.current_question >= len(self.phases[-1]["questions"])
    

    def save_profiles(self):
        """Alias to persist both documents (already handled in apply_responses)."""
        # No-op: updates happen in apply_responses_to_profile
        pass
    
    def submit_answer(self, answer: str):
        """Process a user's answer: apply, save, and advance to next question."""
        q = self.get_current_question()
        if not q:
            return
        field = q['field']
        # Apply and save
        self.apply_responses_to_profile({field: answer}, tier_name=self.phases[self.current_phase]['tier_name'])
        self.save_profiles()
        # Advance pointer
        self.current_question += 1
        # If we've exhausted this phase, move to next
        phase = self.phases[self.current_phase]
        if self.current_question >= len(phase['questions']):
            self.current_phase += 1
            self.current_question = 0


    
    
    def _complete_tier_if_done(self) -> None:
        """
        Look for the first tier whose status is "in_process" but
        all of whose questions have qest == "completed". Mark that
        tier's status to "completed" and save back to Firestore.
        """
        for tier_name, tier in self.tier_questions.items():
            questions = tier.get("questions", [])
            if tier.get("status") == "in_process" and all(
                q.get("qest") == "answered" for q in questions
            ):
                # mark the tier itself completed
                tier["status"] = "completed"
                
                # persist the full tier_questions dict
                db.collection(self.tiers_collection) \
                  .document(self.tiers_doc_id) \
                  .set(self.tier_questions)
                # stop after updating the first matching tier
                break

    def conduct_interview(self):
        """Run through each phase and question, saving answers into both
        the master profile and tier questions via set_nested/apply_responses_to_profile."""
        try:
            while self.current_phase < len(self.phases):
                phase = self.phases[self.current_phase]
                print(f"\n=== {phase['name']} ===\n")
                print(phase['instructions'], "\n")

                while self.current_question < len(phase['questions']):
                    q = phase['questions'][self.current_question]
                    print(f"[Question {self.current_question + 1}] {q['question']}")

                    resp = input("\nYour answer: ").strip()
                    self.conversation.append({
                        "question": q['question'],
                        "answer": resp,
                        "phase": phase['name']
                    })

                    # apply response and save JSONs
                    self.apply_responses_to_profile({q['field']: resp}, phase['tier_name'])
                    with open(self.master_path, 'w') as mf:
                        json.dump(self.master_profile, mf, indent=2)
                    with open(self.tiers_path, 'w') as tf:
                        json.dump(self.tier_questions, tf, indent=2)

                    self.current_question += 1

                self.current_phase += 1
                self.current_question = 0

            print("\nInterview complete! All data saved.")

        except KeyboardInterrupt:
            # On interrupt, still save latest
            with open(self.master_path, 'w') as mf:
                json.dump(self.master_profile, mf, indent=2)
            with open(self.tiers_path, 'w') as tf:
                json.dump(self.tier_questions, tf, indent=2)
            print("\nProgress saved. You can resume later.")






