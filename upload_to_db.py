import streamlit as st
import json
from firebase_admin import credentials, firestore
import firebase_admin

# Initialize Firebase only once
if not firebase_admin._apps:
    firebase_config = st.secrets["firebase"]
    cred = credentials.Certificate(dict(firebase_config))
    firebase_admin.initialize_app(cred)

db = firestore.client()


# helper to check existence
def document_exists(collection_name: str, document_id: str) -> bool:
    doc_ref = db.collection(collection_name).document(document_id)
    return doc_ref.get().exists

# upload function that optionally takes a fixed document_id
def upload_json_data_to_firestore(
    json_data,
    collection_name: str,
    document_id: str = None
):
    """
    If document_id is given, writes the whole json_data under that one document.
    Otherwise, if json_data is a dict: each key→doc_id; if list: auto‐ids each element.
    """
    if document_id:
        # single‐doc mode
        db.collection(collection_name).document(document_id).set(json_data)
        st.success(
            f"Uploaded JSON to '{collection_name}/{document_id}'."
        )
        return

    # no document_id: fall back to bulk behavior
    if isinstance(json_data, dict):
        for doc_id, doc_data in json_data.items():
            db.collection(collection_name).document(doc_id).set(doc_data)
        st.success(
            f"Uploaded {len(json_data)} documents to '{collection_name}/<their keys>'."
        )
    elif isinstance(json_data, list):
        for doc in json_data:
            db.collection(collection_name).add(doc)
        st.success(
            f"Uploaded {len(json_data)} documents to '{collection_name}/<auto IDs>'."
        )
    else:
        st.error("Invalid JSON structure; must be a dict or list of dicts.")









# # Function to check if document exists in Firestore
# def document_exists(collection_name, document_id):
#     doc_ref = db.collection(collection_name).document(document_id)
#     return doc_ref.get().exists

# def upload_json_data_to_firestore(json_data, collection_name):
#     if isinstance(json_data, dict):
#         for doc_id, doc_data in json_data.items():
#             db.collection(collection_name).document(doc_id).set(doc_data)
#     elif isinstance(json_data, list):
#         for doc in json_data:
#             db.collection(collection_name).add(doc)
#     else:
#         st.error("Invalid JSON structure. Must be a dict or list of dicts.")
#         return

#     st.success(f"Uploaded data to Firestore collection: '{collection_name}'")

# # Streamlit UI
# st.title("Upload JSON to Firestore")

# uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
# collection_name = st.text_input("Enter Firestore collection name")

# if uploaded_file and collection_name:
#     try:
#         json_data = json.load(uploaded_file)
#         upload_json_data_to_firestore(json_data, collection_name)
#     except Exception as e:
#         st.error(f"Error uploading JSON: {e}")
