import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import streamlit as st

# Fetching api key
api_key = st.secrets["api"]["key"]

class InterviewAgent:
    def __init__(self, api_key, questions_list, master_path, tiers_path):
        """
        Initialize the interview agent
        
        :param api_key: OpenAI API key
        :param questions_list: List of question dicts from get_pending_questions_by_field
        :param master_path: Path to master_profile.json
        :param tiers_path: Path to general_profile_questions.json
        """
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=200
        )
        # Build dynamic phase structure
        self.phases = [
            {
                "name": "Dynamic Questions",
                "instructions": "Please answer the following questions in order. There are no right or wrong answers.",
                "questions": questions_list,
                "tier_name": "tier1"
            }
        ]
        self.conversation = []
        self.current_phase = 0
        self.current_question = 0
        self.follow_up_depth = 0
        self.master_path = master_path
        self.tiers_path = tiers_path
        
        # Load JSON data
        # with open(self.master_path) as f:
        #     self.master_profile = json.load(f)
        # with open(self.tiers_path) as f:
        #     self.tier_questions = json.load(f)

        with open(self.master_path, 'r', encoding='utf-8') as f:
            self.master_profile = json.load(f)
        with open(self.tiers_path, 'r', encoding='utf-8') as f:
            self.tier_questions = json.load(f)

    def set_nested(self, data: dict, dotted_path: str, value):
        """Set nested dictionary values using dot notation path"""
        keys = dotted_path.split('.')
        d = data
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def apply_responses_to_profile(self, responses: dict, tier_name: str = "tier1"):
        """Update master profile and mark questions as answered"""
        # Update master profile
        for field, answer in responses.items():
            self.set_nested(
                self.master_profile["generalprofile"],
                field,
                answer
            )
        
        # Update question status in tier questions
        questions = self.tier_questions.get(tier_name, {}).get("questions", [])
        for q in questions:
            if q.get("field") in responses and q.get("qest") == "pending":
                q["qest"] = "answered"

    # def save_profiles(self):
    #     """Persist changes to JSON files"""
    #     with open(self.master_path, 'w') as mf:
    #         json.dump(self.master_profile, mf, indent=2)
    #     with open(self.tiers_path, 'w') as tf:
    #         json.dump(self.tier_questions, tf, indent=2)

    def save_profiles(self):
        with open(self.master_path, 'w', encoding='utf-8') as mf:
            json.dump(self.master_profile, mf, indent=2, ensure_ascii=False)
        with open(self.tiers_path, 'w', encoding='utf-8') as tf:
            json.dump(self.tier_questions, tf, indent=2, ensure_ascii=False)

    def _needs_elaboration(self, response):
        """Check if response needs follow-up using multiple criteria"""
        if len(response.split()) < 30:
            return True
        return self._llm_assessment(response)

    def _llm_assessment(self, response):
        """Use LLM to assess response quality"""
        prompt = f"""Assess if this response needs follow-up (Answer only YES/NO):
        Response: {response[:500]}  # Truncate to save tokens
        Consider: Specific examples? Emotional depth? Concrete details?"""
        return self.llm([HumanMessage(content=prompt)]).content == "YES"

    def _generate_follow_up(self, question, response):
        """Generate context-aware follow-up question"""
        prompt = f"""Generate ONE follow-up question based on:
        Original Q: {question}
        Response: {response[:300]}
        Keep it relevant and probing. Format: 'Follow-up: ...'"""
        result = self.llm([HumanMessage(content=prompt)]).content
        return result.replace("Follow-up: ", "").strip()

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

                    # Get initial response
                    resp = input("\nYour answer: ").strip()
                    self.conversation.append({
                        "question": q['question'],
                        "answer": resp,
                        "phase": phase['name'],
                        "field": q['field']
                    })

                    # Follow-up logic
                    self.follow_up_depth = 0
                    full_response = resp  # Start with initial response
                    
                    while self._needs_elaboration(full_response) and self.follow_up_depth < 2:
                        follow_up = self._generate_follow_up(q['question'], full_response)
                        print(f"\n[Follow-up] {follow_up}")
                        follow_resp = input("Your answer: ").strip()
                        
                        self.conversation.append({
                            "question": follow_up,
                            "answer": follow_resp,
                            "phase": phase['name'],
                            "field": q['field']  # Same field as original question
                        })
                        full_response += " " + follow_resp
                        self.follow_up_depth += 1

                    # Apply response to both profiles
                    self.apply_responses_to_profile(
                        {q['field']: full_response}, 
                        phase['tier_name']
                    )
                    self.save_profiles()

                    self.current_question += 1

                self.current_phase += 1
                self.current_question = 0

            print("\nInterview complete! All data saved.")

        except KeyboardInterrupt:
            # On interrupt, still save latest
            self.save_profiles()
            print("\nProgress saved. You can resume later.")


    def get_current_question(self):
        """Return the current question dict, or None if interview is finished."""
        if self.current_phase >= len(self.phases):
            return None
        phase = self.phases[self.current_phase]
        if self.current_question >= len(phase["questions"]):
            return None
        return phase["questions"][self.current_question]

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
