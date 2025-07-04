# # # import streamlit as st
# # # import firebase_admin
# # # from firebase_admin import credentials, firestore
# # # from upload_to_db import upload_json_data_to_firestore, document_exists
# # # import json

# # # # Fetching API keys and configs
# # # openai_key = st.secrets["api"]["key"]
# # # firebase_config = st.secrets["firebase"]

# # # # Setting up Firebase
# # # cred = credentials.Certificate(dict(firebase_config))
# # # if not firebase_admin._apps:
# # #     firebase_admin.initialize_app(cred)
# # # db = firestore.client()

# # # # Main Title
# # # st.markdown(
# # #     '<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>',
# # #     unsafe_allow_html=True
# # # )

# # # # Sidebar UI
# # # with st.sidebar:
# # #     # Logo
# # #     st.image("logo trans.png", width=200)

# # #     # Custom Button Styles
# # #     st.markdown("""
# # #     <style>
# # #         .stButton button {
# # #             background-color: #2c2c2e;
# # #             color: white;
# # #             font-size: 16px;
# # #             padding: 8px 20px;
# # #             border-radius: 5px;
# # #             border: none;
# # #             cursor: pointer;
# # #             transition: all 0.3s ease;
# # #         }
# # #         .stButton button:hover {
# # #             background-color: #95A5A6;
# # #         }
# # #         .stButton button:active {
# # #             background-color: #BDC3C7;
# # #         }
# # #     </style>
# # #     """, unsafe_allow_html=True)

# # #     # JSON Upload Section
# # #     st.title("Upload JSON to Firestore")
# # #     collection_name = st.text_input("Enter Firestore collection name")
# # #     uploaded_file = st.file_uploader("Upload JSON file", type=["json"])


# # #     if uploaded_file and collection_name:
# # #     # derive a document_id from the file name
# # #         file_name = uploaded_file.name.rsplit(".", 1)[0]

# # #         # check existence
# # #         if document_exists(collection_name, file_name):
# # #             st.warning(
# # #                 f"A document with ID '{file_name}' already exists in collection '{collection_name}'."
# # #             )
# # #         else:
# # #             try:
# # #                 json_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
# # #                 upload_json_data_to_firestore(
# # #                     json_data,
# # #                     collection_name,
# # #                     document_id=file_name
# # #                 )
# # #             except Exception as e:
# # #                 st.error(f"Error uploading JSON: {e}")


# # #     # Profile Download Button
# # #     if st.button("Profile"):
# # #         doc_ref = db.collection("profiles").document("current_user")
# # #         doc = doc_ref.get()
# # #         if doc.exists:
# # #             profile_data = doc.to_dict()
# # #             profile_str = json.dumps(profile_data, indent=4)
# # #             st.download_button(
# # #                 label="Download Profile",
# # #                 data=profile_str,
# # #                 file_name="profile.txt",
# # #                 mime="text/plain"
# # #             )
# # #         else:
# # #             st.error("Take the interview first!")

# # #     # Interview Agent Reset Button
# # #     if st.button("Interview Agent"):
# # #         doc_ref = db.collection("profiles").document("current_user")
# # #         doc_ref.delete()
# # #         st.experimental_rerun()




# # # # Add to your existing imports
# # # import tempfile
# # # from interview_agent import InterviewAgent, run_interview_agent
# # # from quest import get_pending_questions_by_field
# # # import streamlit as st 


# # # # Add to your secrets
# # # firebase_config = st.secrets["firebase"]
# # # openai_key = st.secrets["api"]["key"]

# # # # Main chat area
# # # st.markdown("---")
# # # st.subheader("Prism Interview Agent")

# # # # Initialize session state
# # # if "interview_state" not in st.session_state:
# # #     st.session_state.interview_state = {
# # #         "active": False,
# # #         "current_question": None,
# # #         "messages": [],
# # #         "agent": None
# # #     }

# # # # Create temporary files for interview process
# # # if "temp_files_created" not in st.session_state:
# # #     with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_master, \
# # #          tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_tiers:
        
# # #         # Initialize with default structure
# # #         default_master = {"generalprofile": {
# # #             "corePreferences": {
# # #                 "noveltySeeking": "",
# # #                 "leisureMotivation": "",
# # #                 "decisionStyle": "",
# # #                 "semanticTraits": [""]
# # #             },
# # #             "userContextAndLifestyle": {
# # #                 "userLocation": {
# # #                     "specificCity": "",
# # #                     "specificArea": "",
# # #                     "specificNeibhourhood": ""
# # #                 }
# # #             }
# # #         }}
        
# # #         default_tiers = {
# # #             "tier1": {
# # #                 "status": "in_process",
# # #                 "questions": []
# # #             }
# # #         }
        
# # #         json.dump(default_master, tmp_master)
# # #         json.dump(default_tiers, tmp_tiers)
        
# # #         st.session_state.temp_master = tmp_master.name
# # #         st.session_state.temp_tiers = tmp_tiers.name
# # #         st.session_state.temp_files_created = True

# # # # Start interview button
# # # if not st.session_state.interview_state["active"]:
# # #     if st.button("Start New Interview"):
# # #         # Get pending questions from Firestore
# # #         try:
# # #             # Get latest questions from Firestore
# # #             doc_ref = db.collection("questionnaires").document("current_profile")
# # #             doc = doc_ref.get()
# # #             if doc.exists:
# # #                 tier_questions = doc.to_dict()
# # #                 with open(st.session_state.temp_tiers, "w") as f:
# # #                     json.dump(tier_questions, f)
                
# # #                 # Get pending questions
# # #                 pending_questions = get_pending_questions_by_field(st.session_state.temp_tiers)
                
# # #                 if pending_questions:
# # #                     # Initialize agent
# # #                     agent = run_interview_agent(
# # #                         pending_questions,
# # #                         st.session_state.temp_master,
# # #                         st.session_state.temp_tiers,
# # #                         openai_key
# # #                     )
                    
# # #                     # Update session state
# # #                     st.session_state.interview_state = {
# # #                         "active": True,
# # #                         "current_question": agent.get_current_question(),
# # #                         "messages": [{
# # #                             "role": "assistant", 
# # #                             "content": "Welcome to the Prism interview! Let's begin."
# # #                         }],
# # #                         "agent": agent
# # #                     }
# # #                     st.rerun()
# # #                 else:
# # #                     st.warning("No pending questions found!")
# # #             else:
# # #                 st.error("Questionnaire not found in Firestore!")
# # #         except Exception as e:
# # #             st.error(f"Error starting interview: {str(e)}")

# # # # Interview chat interface
# # # if st.session_state.interview_state["active"]:
# # #     agent = st.session_state.interview_state["agent"]
    
# # #     # Display chat messages
# # #     for msg in st.session_state.interview_state["messages"]:
# # #         with st.chat_message(msg["role"]):
# # #             st.write(msg["content"])
    
# # #     # Handle current question
# # #     current_q = st.session_state.interview_state["current_question"]
# # #     if current_q:
# # #         # Display current question
# # #         with st.chat_message("assistant"):
# # #             st.write(current_q['question'])
        
# # #         # Get user response
# # #         if prompt := st.chat_input("Type your answer here..."):
# # #             # Add user message to chat
# # #             st.session_state.interview_state["messages"].append({
# # #                 "role": "user", 
# # #                 "content": prompt
# # #             })
            
# # #             # Submit answer
# # #             agent.submit_answer(prompt)
            
# # #             # Check if interview is complete
# # #             if agent.is_complete():
# # #                 # Save final profile to Firestore
# # #                 with open(st.session_state.temp_master) as f:
# # #                     master_data = json.load(f)
                
# # #                 db.collection("profiles").document("current_user").set(master_data)
                
# # #                 # Update session state
# # #                 st.session_state.interview_state["messages"].append({
# # #                     "role": "assistant", 
# # #                     "content": "✅ Interview complete! Your profile has been saved."
# # #                 })
# # #                 st.session_state.interview_state["active"] = False
# # #                 st.rerun()
# # #             else:
# # #                 # Get next question
# # #                 next_q = agent.get_current_question()
# # #                 st.session_state.interview_state["current_question"] = next_q
# # #                 st.session_state.interview_state["messages"].append({
# # #                     "role": "assistant", 
# # #                     "content": next_q['question']
# # #                 })
# # #                 st.rerun()
# # #     else:
# # #         st.session_state.interview_state["active"] = False
# # #         st.error("Interview completed unexpectedly")



# # import streamlit as st
# # import firebase_admin
# # from firebase_admin import credentials, firestore
# # from upload_to_db import upload_json_data_to_firestore, document_exists
# # import json
# # import tempfile
# # import os
# # from interview_agent import InterviewAgent  # We'll create this module
# # from twin import generate_recommendations, load_user_profile

# # # Fetching API keys and configs
# # openai_key = st.secrets["api"]["key"]
# # firebase_config = st.secrets["firebase"]

# # # Setting up Firebase
# # cred = credentials.Certificate(dict(firebase_config))
# # if not firebase_admin._apps:
# #     firebase_admin.initialize_app(cred)
# # db = firestore.client()

# # # Main Title
# # st.markdown(
# #     '<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>',
# #     unsafe_allow_html=True
# # )

# # # Sidebar UI
# # with st.sidebar:
# #     # Logo
# #     st.image("logo trans.png", width=200)

# #     # Custom Button Styles
# #     st.markdown("""
# #     <style>
# #         .stButton button {
# #             background-color: #2c2c2e;
# #             color: white;
# #             font-size: 16px;
# #             padding: 8px 20px;
# #             border-radius: 5px;
# #             border: none;
# #             cursor: pointer;
# #             transition: all 0.3s ease;
# #         }
# #         .stButton button:hover {
# #             background-color: #95A5A6;
# #         }
# #         .stButton button:active {
# #             background-color: #BDC3C7;
# #         }
# #     </style>
# #     """, unsafe_allow_html=True)

# #     # JSON Upload Section
# #     st.title("Upload JSON to Firestore")
# #     collection_name = st.text_input("Enter Firestore collection name")
# #     uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

# #     if uploaded_file and collection_name:
# #         # derive a document_id from the file name
# #         file_name = uploaded_file.name.rsplit(".", 1)[0]

# #         # check existence
# #         if document_exists(collection_name, file_name):
# #             st.warning(
# #                 f"A document with ID '{file_name}' already exists in collection '{collection_name}'."
# #             )
# #         else:
# #             try:
# #                 json_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
# #                 upload_json_data_to_firestore(
# #                     json_data,
# #                     collection_name,
# #                     document_id=file_name
# #                 )
# #                 st.success("JSON uploaded successfully!")
# #             except Exception as e:
# #                 st.error(f"Error uploading JSON: {e}")

# #     # Profile Download Button
# #     if st.button("Profile"):
# #         doc_ref = db.collection("profiles").document("current_user")
# #         doc = doc_ref.get()
# #         if doc.exists:
# #             profile_data = doc.to_dict()
# #             profile_str = json.dumps(profile_data, indent=4)
# #             st.download_button(
# #                 label="Download Profile",
# #                 data=profile_str,
# #                 file_name="profile.json",
# #                 mime="application/json"
# #             )
# #         else:
# #             st.error("No profile found! Complete the interview first.")

# #     if st.button("Get Recommedation"):
# #         # ==== New: Recommendation Section ==== 
# #         st.markdown("---")
# #         st.subheader("Personalized Recommendations")

# #         # Only show if profile exists
# #         if st.button("Load Profile & Ask Recommendation"):
# #             profile = load_user_profile()
# #             if not profile:
# #                 st.error("No user profile found. Please complete the interview first.")
# #             else:
# #                 # Prompt user for a recommendation query
# #                 user_query = st.text_input("What would you like recommendations for?", key="rec_query")
# #                 if user_query:
# #                     with st.spinner("Generating recommendations..."):
# #                         try:
# #                             recs_json = generate_recommendations(profile, user_query)
# #                             # Parse JSON string
# #                             recs = json.loads(recs_json)
# #                             # Display each recommendation
# #                             for idx, item in enumerate(recs, 1):
# #                                 st.markdown(f"**{idx}. {item['title']}**")
# #                                 st.write(item['reason'])
# #                         except Exception as e:
# #                             st.error(f"Failed to generate recommendations: {e}")

# #         # ==== Footer / End ==== 
# #         st.markdown("---")


# #     # Interview Agent Reset Button
# #     if st.button("Reset Interview"):
# #         if "interview_agent" in st.session_state:
# #             del st.session_state.interview_agent
# #         if "interview_messages" in st.session_state:
# #             del st.session_state.interview_messages
# #         st.success("Interview reset! You can start a new one.")
# #         st.experimental_rerun()

# # # Create a new file called interview_agent.py
# # st.subheader("Prism Interview Agent")
# # st.write("Answer questions to build your personalized profile")

    

# # # Initialize session state
# # if "interview_messages" not in st.session_state:
# #     st.session_state.interview_messages = []

# # # Create temporary files for interview process
# # # if "temp_files_created" not in st.session_state:
# # #     with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_master, \
# # #          tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_tiers:
        
# # #         # Initialize with default structure
# # #         default_master = {"generalprofile": {
# # #             "corePreferences": {
# # #                 "noveltySeeking": "",
# # #                 "leisureMotivation": "",
# # #                 "decisionStyle": "",
# # #                 "semanticTraits": [""]
# # #             },
# # #             "userContextAndLifestyle": {
# # #                 "userLocation": {
# # #                     "specificCity": "",
# # #                     "specificArea": "",
# # #                     "specificNeibhourhood": ""
# # #                 }
# # #             }
# # #         }}
        
# # #         # Load actual structure from your general_profile_questions.json
# # #         try:
# # #             with open("general_questions (2).json") as f:
# # #                 default_tiers = json.load(f)
# # #         except:
# # #             default_tiers = {
# # #                 "tier1": {
# # #                     "status": "in_process",
# # #                     "questions": []
# # #                 }
# # #             }
        
# # #         json.dump(default_master, tmp_master)
# # #         json.dump(default_tiers, tmp_tiers)
        
# # #         st.session_state.temp_master = tmp_master.name
# # #         st.session_state.temp_tiers = tmp_tiers.name
# # #         st.session_state.temp_files_created = True


# # if "temp_files_created" not in st.session_state:
# #     # Create text mode files instead of binary
# #     with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmp_master, \
# #          tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmp_tiers:
        
# #         # Initialize with default structure
# #         default_master = {"generalprofile": {
# #             "corePreferences": {
# #                 "noveltySeeking": "",
# #                 "leisureMotivation": "",
# #                 "decisionStyle": "",
# #                 "semanticTraits": [""]
# #             },
# #             "userContextAndLifestyle": {
# #                 "userLocation": {
# #                     "specificCity": "",
# #                     "specificArea": "",
# #                     "specificNeibhourhood": ""
# #                 }
# #             }
# #         }}
        
# #         # Load actual structure from your general_profile_questions.json
# #         try:
# #             with open("general_questions (2).json", 'r', encoding='utf-8') as f:
# #                 default_tiers = json.load(f)
# #         except Exception as e:
# #             st.error(f"Error loading question structure: {str(e)}")
# #             default_tiers = {
# #                 "tier1": {
# #                     "status": "in_process",
# #                     "questions": []
# #                 }
# #             }
        
# #         json.dump(default_master, tmp_master, ensure_ascii=False)
# #         json.dump(default_tiers, tmp_tiers, ensure_ascii=False)
        
# #         # Flush to ensure data is written
# #         tmp_master.flush()
# #         tmp_tiers.flush()
        
# #         st.session_state.temp_master = tmp_master.name
# #         st.session_state.temp_tiers = tmp_tiers.name
# #         st.session_state.temp_files_created = True






# # from quest_generate import get_pending_questions_by_field



# # # Initialize or resume interview
# # if "interview_agent" not in st.session_state:
# #     # Get pending questions
# #     pending_questions = get_pending_questions_by_field(st.session_state.temp_tiers)
    
# #     if pending_questions:
# #         # Convert to questions list format
# #         questions_list = [
# #             {"field": field, "question": question_text}
# #             for field, question_text in pending_questions.items()
# #         ]
        
# #         # Initialize agent
# #         agent = InterviewAgent(
# #             api_key=openai_key,
# #             questions_list=questions_list,
# #             master_path=st.session_state.temp_master,
# #             tiers_path=st.session_state.temp_tiers
# #         )
# #         st.session_state.interview_agent = agent
# #         st.session_state.interview_messages.append({
# #             "role": "assistant", 
# #             "content": "Welcome to the Prism interview! I'll ask questions to build your profile."
# #         })
# #         # Add first question
# #         first_question = agent.get_current_question()
# #         if first_question:
# #             st.session_state.interview_messages.append({
# #                 "role": "assistant", 
# #                 "content": first_question['question']
# #             })
# #     else:
# #         st.info("No pending questions found! Your profile is complete.")

# # # Display chat messages
# # for msg in st.session_state.interview_messages:
# #     with st.chat_message(msg["role"]):
# #         st.write(msg["content"])

# # # Handle user input
# # if "interview_agent" in st.session_state and st.session_state.interview_agent:
# #     agent = st.session_state.interview_agent
    
# #     if prompt := st.chat_input("Type your answer here..."):
# #         # Add user message
# #         st.session_state.interview_messages.append({
# #             "role": "user", 
# #             "content": prompt
# #         })
        
# #         # Submit answer to agent
# #         agent.submit_answer(prompt)
        
# #         # Check if interview is complete
# #         if agent.is_complete():
# #             # Save final profile to Firestore
# #             with open(st.session_state.temp_master) as f:
# #                 master_data = json.load(f)
            
# #             db.collection("profiles").document("current_user").set(master_data)
            
# #             # Completion message
# #             st.session_state.interview_messages.append({
# #                 "role": "assistant", 
# #                 "content": "✅ Interview complete! Your profile has been saved."
# #             })
# #             st.rerun()
# #         else:
# #             # Get next question
# #             next_q = agent.get_current_question()
# #             if next_q:
# #                 st.session_state.interview_messages.append({
# #                     "role": "assistant", 
# #                     "content": next_q['question']
# #                 })
# #                 st.rerun()
# #             else:
# #                 st.session_state.interview_messages.append({
# #                     "role": "assistant", 
# #                     "content": "⚠️ No more questions found. Interview completed."
# #                 })
# #                 st.rerun()



# import streamlit as st
# import firebase_admin
# from firebase_admin import credentials, firestore
# from upload_to_db import upload_json_data_to_firestore, document_exists
# import json
# import tempfile
# import os

# from interview_agent import InterviewAgent
# from twin import load_user_profile, generate_recommendations
# from quest_generate import get_pending_questions_by_field

# # --- CONFIG & FIREBASE SETUP ---
# openai_key     = st.secrets["api"]["key"]
# firebase_config = st.secrets["firebase"]

# cred = credentials.Certificate(dict(firebase_config))
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# # --- PAGE TITLE ---
# st.markdown(
#     '<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>',
#     unsafe_allow_html=True
# )

# # --- SESSION STATE FLAGS ---
# if "show_recs" not in st.session_state:
#     st.session_state.show_recs = False
# if "interview_messages" not in st.session_state:
#     st.session_state.interview_messages = []

# # --- SIDEBAR ---
# with st.sidebar:
#     st.image("logo trans.png", width=200)

#     # custom button styling
#     st.markdown("""
#     <style>
#       .stButton button {
#         background-color: #2c2c2e;
#         color: white;
#         font-size: 16px;
#         padding: 8px 20px;
#         border-radius: 5px;
#         border: none;
#         cursor: pointer;
#         transition: all 0.3s ease;
#       }
#       .stButton button:hover { background-color: #95A5A6; }
#       .stButton button:active { background-color: #BDC3C7; }
#     </style>""", unsafe_allow_html=True)

#     # JSON uploader
#     st.title("Upload JSON")
#     collection_name = st.text_input("Firestore collection")
#     uploaded_file   = st.file_uploader("JSON file", type=["json"])
#     if uploaded_file and collection_name:
#         doc_id = uploaded_file.name.rsplit(".",1)[0]
#         if document_exists(collection_name, doc_id):
#             st.warning(f"‘{doc_id}’ exists in '{collection_name}'")
#         else:
#             try:
#                 data = json.loads(uploaded_file.getvalue().decode("utf-8"))
#                 upload_json_data_to_firestore(data, collection_name, document_id=doc_id)
#                 st.success("Uploaded!")
#             except Exception as e:
#                 st.error(f"Upload error: {e}")

#     if st.button("Delete Profile"):
#         try:
#             # Remove from Firestore
#             db.collection("profiles").document("current_user").delete()
#             # Clear any local state
#             for key in ["interview_agent", "interview_messages", "profile_loaded"]:
#                 if key in st.session_state:
#                     del st.session_state[key]
#             st.success("✔️ Profile deleted from Firebase.")
#         except Exception as e:
#             st.error(f"Failed to delete profile: {e}")

#     # Download profile
#     if st.button("Download Profile"):
#         doc = db.collection("profiles").document("current_user").get()
#         if doc.exists:
#             profile_str = json.dumps(doc.to_dict(), indent=2)
#             st.download_button("Download JSON", data=profile_str,
#                                file_name="profile.json", mime="application/json")
#         else:
#             st.error("No profile—run the interview first.")

#     # Switch to Recommendation mode
#     if st.sidebar.button("Get Recommendation"):
#         st.session_state.show_recs = True

#     # Reset everything
#     if st.sidebar.button("Reset Interview"):
#         for key in ["interview_messages", "interview_agent", "show_recs"]:
#             if key in st.session_state:
#                 del st.session_state[key]
#         st.rerun()

# # --- MAIN PAGE CONTENT ---
# st.markdown("---")

# # if st.session_state.show_recs:
# if "show_recs" in st.session_state and st.session_state.show_recs:
#     # --------------- RECOMMENDATION UI ---------------
#     st.subheader("Personalized Recommendations")

#     # Load profile once
#     if "profile_loaded" not in st.session_state:
#         st.session_state.profile_loaded = load_user_profile()

#     if not st.session_state.profile_loaded:
#         st.error("No profile found—complete the interview first.")
#     else:
#         # ask for query
#         query = st.text_input("What would you like recommendations for?", key="rec_query")
#         if st.button("Generate Recommendations"):
#             with st.spinner("Thinking…"):
#                 try:
#                     recs_json = generate_recommendations(st.session_state.profile_loaded, query)
#                     recs = json.loads(recs_json)
#                     for i, item in enumerate(recs, 1):
#                         st.markdown(f"**{i}. {item['title']}**")
#                         st.write(item["reason"])
#                 except Exception as err:
#                     st.error(f"Failed: {err}")

#     # “Back” button
#     if st.button("← Back to Interview"):
#         st.session_state.show_recs = False
#         st.rerun()

# else:
#     # --------------- INTERVIEW UI ---------------
#     st.subheader("Prism Interview Agent")
#     st.write("Answer questions to build your profile:")

#     # Prepare temp files once
#     if "temp_files_created" not in st.session_state:
#         with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as m, \
#              tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as t:
#             # default master
#             default_master = {
#                 "generalprofile": {
#                     "corePreferences": {
#                         "noveltySeeking": "",
#                         "leisureMotivation": "",
#                         "decisionStyle": "",
#                         "semanticTraits": [""]
#                     },
#                     "userContextAndLifestyle": {
#                         "userLocation": {
#                             "specificCity": "",
#                             "specificArea": "",
#                             "specificNeibhourhood": ""
#                         }
#                     }
#                 }
#             }
#             json.dump(default_master, m, ensure_ascii=False)
#             # load tier questions
#             try:
#                 tiers = json.load(open("general_questions (2).json", encoding='utf-8'))
#             except:
#                 tiers = {"tier1": {"status": "in_process", "questions": []}}
#             json.dump(tiers, t, ensure_ascii=False)
#             st.session_state.temp_master = m.name
#             st.session_state.temp_tiers = t.name
#             st.session_state.temp_files_created = True

#     # Initialize agent once
#     if "interview_agent" not in st.session_state:
#         pending = get_pending_questions_by_field(st.session_state.temp_tiers)
#         if pending:
#             qlist = [{"field": f, "question": txt} for f, txt in pending.items()]
#             agent = InterviewAgent(openai_key, qlist,
#                                    st.session_state.temp_master,
#                                    st.session_state.temp_tiers)
#             st.session_state.interview_agent = agent
#             st.session_state.interview_messages = [
#                 {"role": "assistant", "content": "Welcome! Let's build your profile."},
#                 {"role": "assistant", "content": agent.get_current_question()["question"]}
#             ]
#         else:
#             st.info("No pending questions—profile complete.")

#     # Render chat
#     for msg in st.session_state.interview_messages:
#         with st.chat_message(msg["role"]):
#             st.write(msg["content"])

#     # Handle user reply
#     # if st.session_state.interview_agent:
#     if "interview_agent" in st.session_state and st.session_state.interview_agent:
#         if reply := st.chat_input("Your answer…"):
#             st.session_state.interview_messages.append({"role": "user", "content": reply})
#             agent = st.session_state.interview_agent
#             agent.submit_answer(reply)

#             if agent.is_complete():
#                 # save to Firestore
#                 master_data = json.load(open(st.session_state.temp_master))
#                 db.collection("profiles").document("current_user").set(master_data)
#                 st.session_state.interview_messages.append({
#                     "role": "assistant",
#                     "content": "✅ Interview complete! Profile saved."
#                 })
#             else:
#                 # next_q = agent.get_current_question()
#                 # st.session_state.interview_messages.append({
#                 #     "role": "assistant", "content": next_q["question"]
#                 # })

#                 next_q = agent.get_current_question()

#                 if next_q and "question" in next_q:
#                     st.session_state.interview_messages.append({
#                         "role": "assistant",
#                         "content": next_q["question"]
#                     })
#                 else:
#                     st.session_state.interview_messages.append({
#                         "role": "assistant",
#                         "content": "⚠️ No more questions. Interview is complete."
#                     })

#             st.rerun()



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

    # JSON uploader
    st.title("Upload JSON")
    collection_name = st.text_input("Firestore collection")
    uploaded_file   = st.file_uploader("JSON file", type=["json"])

    if st.button("List collections"):
        # if collection_name:
        #     docs = db.collection(collection_name).list_documents()
        # else:
        #     st.warning("Please select a collection first.")
        collections = db.collections()
        st.write("📂 Available collections:", [c.id for c in collections])


    if uploaded_file and collection_name:
        doc_id = uploaded_file.name.rsplit(".",1)[0]
        if document_exists(collection_name, doc_id):
            st.warning(f"‘{doc_id}’ exists in '{collection_name}'")
        else:
            try:
                data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                upload_json_data_to_firestore(data, collection_name, document_id=doc_id)
                st.success("Uploaded!")
                st.write("✅ Uploaded to:", f"{collection_name}/{doc_id}")
            except Exception as e:
                st.error(f"Upload error: {e}")

    if st.button("check profile"):
        try:
            doc_ref = db.collection(collection_name).document("users")
            snapshot = doc_ref.get()
            if snapshot.exists:
                st.write("✅ Profile exists in Firestore.")
            else:
                st.write("❌ No such profile document.")
        except Exception as e:
            st.error(f"Insert collection name first {e}")

    if st.button("Delete Profile"):
        try:
            # Remove from Firestore
            db.collection("profiles").document("users").delete()
            # Clear any local state
            for key in ["interview_agent", "interview_messages", "profile_loaded"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✔️ Profile deleted from Firebase.")
        except Exception as e:
            st.error(f"Failed to delete profile: {e}")

    # Download profile
    if st.button("Download Profile"):
        doc = db.collection("profiles").document("users").get()
        if doc.exists:
            profile_str = json.dumps(doc.to_dict(), indent=2)
            st.download_button("Download JSON", data=profile_str,
                               file_name="profile.json", mime="application/json")
        else:
            st.error("No profile—run the interview first.")

    # Switch to Recommendation mode
    if st.sidebar.button("Get Recommendation"):
        st.session_state.show_recs = True

    # Reset everything
    if st.sidebar.button("Reset Interview"):
        for key in ["interview_messages", "interview_agent", "show_recs"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Add to sidebar
    if st.sidebar.button("Debug Questions"):
        doc = db.collection("questionnaires").document("users").get()
        if doc.exists:
            data = doc.to_dict()
            st.write("Questionnaire Data:", data)
            st.write("Pending Questions:", get_pending_questions_by_field(data))
        else:
            st.error("No questionnaire found")

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
                    for i, item in enumerate(recs, 1):
                        st.markdown(f"**{i}. {item['title']}**")
                        st.write(item["reason"])
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

    # Initialize agent once
    if "interview_agent" not in st.session_state:
        # load from Firestore
        # master_doc = db.collection("profiles").document("current_user").get()
        # tier_doc = db.collection("questionnaires").document("current_user").get()
        # if master_doc.exists and tier_doc.exists:
        #     master_data = master_doc.to_dict()
        #     tier_data = tier_doc.to_dict()
        # else:
        #     master_data = {
        #         "generalprofile": {
        #             "corePreferences": {
        #                 "noveltySeeking": "",
        #                 "leisureMotivation": "",
        #                 "decisionStyle": "",
        #                 "semanticTraits": [""]
        #             },
        #             "userContextAndLifestyle": {
        #                 "userLocation": {
        #                     "specificCity": "",
        #                     "specificArea": "",
        #                     "specificNeibhourhood": ""
        #                 }
        #             }
        #         }
        #     }
        #     tier_data = {"tier1": {"status": "in_process", "questions": []}}

        # pending = get_pending_questions_by_field(tier_data)

        master_doc = db.collection("profiles").document("users").get()
        tier_doc   = db.collection("questionnaires").document("users").get()

        # Flag to drive your UI logic
        needs_profile_upload = False

        if master_doc.exists and tier_doc.exists:
            master_data = master_doc.to_dict()
            tier_data   = tier_doc.to_dict()
        else:
            # We won’t auto‑create any blank data;
            # instead, let the front end know to ask the user to upload their profile
            needs_profile_upload = True
            master_data = None
            tier_data   = None

        if needs_profile_upload:
            # e.g. in Streamlit you could show st.file_uploader or a button
            st.warning("Please upload your profile and questionnaire to get started.")
        else:
            pending = get_pending_questions_by_field(tier_data)


            if pending:
                qlist = [{"field": f, "question": txt} for f, txt in pending.items()]
                agent = InterviewAgent(openai_key, qlist, master_data, tier_data)
                st.session_state.interview_agent = agent
                st.session_state.interview_messages = [
                    {"role": "assistant", "content": "Welcome! Let's build your profile."},
                    {"role": "assistant", "content": agent.get_current_question()["question"]}
                ]
            else:
                st.info("No pending questions—profile complete.")

    # Render chat
    for msg in st.session_state.interview_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Handle user reply
    if "interview_agent" in st.session_state and st.session_state.interview_agent:
        if reply := st.chat_input("Your answer…"):
            st.session_state.interview_messages.append({"role": "user", "content": reply})
            agent = st.session_state.interview_agent
            agent.submit_answer(reply)

            # Save progress after each step
            db.collection("profiles").document("users").set(agent.master_profile)
            db.collection("questionnaires").document("users").set(agent.tier_questions)

            if agent.is_complete():
                st.session_state.interview_messages.append({
                    "role": "assistant",
                    "content": "✅ Interview complete! Profile saved."
                })
            else:
                next_q = agent.get_current_question()
                if next_q and "question" in next_q:
                    st.session_state.interview_messages.append({
                        "role": "assistant",
                        "content": next_q["question"]
                    })
                else:
                    st.session_state.interview_messages.append({
                        "role": "assistant",
                        "content": "⚠️ No more questions. Interview is complete."
                    })

            st.rerun()
