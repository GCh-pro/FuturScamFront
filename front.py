import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from params import MONGO_URI, DB_NAME, COLLECTION_NAME
from test import load_skill_terms, create_extractor, extract_skills
import uuid

# -------------------------------------
# ----------- CUSTOM STYLE ------------
# -------------------------------------

st.markdown(""" 
    <style>
        body { background-color: #11161C !important; }
        .stApp { background-color: #11161C !important; }
        h1, h2, h3, h4, h5 { color: white !important; }
        p, label, span { color: #E6E6E6 !important; }
        section[data-testid="stSidebar"] {
            background-color: #0D1117 !important;
            border-right: 1px solid #2A2F36;
        }
        section[data-testid="stSidebar"] * { color: #E6E6E6 !important; }
        .stButton>button {
            background-color: #F68A34 !important; color: white !important;
            border-radius: 8px !important; padding: 0.6rem 1.2rem !important;
            border: none !important; font-weight: 600;
        }
        .stButton>button:hover { background-color: #ff9b48 !important; }
        hr { border: 1px solid #2D323A !important; }
        .stTextInput>div>div>input,
        .stTextArea textarea {
            background-color: #1A1F26 !important; color: #F2F2F2 !important;
            border: 1px solid #333943 !important; border-radius: 6px !important;
        }
    </style>
""", unsafe_allow_html=True)



# -------------------------------------
# ---------------- HEADER -------------
# -------------------------------------

try:
    st.image("logo.png", width=800)
except FileNotFoundError:
    st.warning("Logo file not found")
st.markdown("<h1 style='color:white; margin-top: 20px;'>RFP Manager</h1>", unsafe_allow_html=True)



# -------------------------------------
# ----------- DB CONNECTION -----------
# -------------------------------------

@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

collection = get_collection()



# -------------------------------------
# ----------- NAVIGATION --------------
# -------------------------------------

query = st.query_params.to_dict()
page = query.get("page", "list")
doc_id = query.get("id")

def go_to(page_name, **params):
    st.query_params.clear()
    st.query_params["page"] = page_name
    for k, v in params.items():
        st.query_params[k] = v

menu = st.sidebar.selectbox("Navigation", ["RFP List", "Add New RFP"])

if menu == "RFP List" and page != "detail":
    go_to("list")

if menu == "Add New RFP":
    go_to("new")



# -------------------------------------
# ----------- PAGE: LIST --------------
# -------------------------------------

if page == "list":
    st.subheader("All RFPs")
    docs = list(collection.find())

    if not docs:
        st.info("No documents found.")
    else:
        for doc in docs:
            title = doc.get("roleTitle", "Unknown role")
            company = doc.get("company", {}).get("name", "Unknown company")
            doc_id_str = str(doc["_id"])

            if st.button(f"{title} — {company}", key=doc_id_str):
                go_to("detail", id=doc_id_str)

    st.divider()

    if st.button("➕ Add RFP"):
        go_to("new")



# -------------------------------------
# ----------- PAGE: DETAIL ------------
# -------------------------------------

elif page == "detail" and doc_id:
    doc = collection.find_one({"_id": ObjectId(doc_id)})

    if not doc:
        st.error("Document not found.")
    else:
        st.subheader(doc.get("roleTitle", "RFP Detail"))

        st.markdown("### Company")
        st.markdown(doc.get("company", {}))

        st.markdown("### Conditions")
        st.markdown(doc.get("conditions", {}))

        st.markdown("### Languages")
        st.markdown(doc.get("languages", []))

        st.markdown("### Skills")
        st.markdown(doc.get("skills", []))

        st.markdown("### Job Description")
        st.markdown(doc.get("job_desc", ""), unsafe_allow_html=True)

    st.divider()

    if st.button("⬅ Back to list"):
        go_to("list")



# -------------------------------------
# ----------- PAGE: NEW ---------------
# -------------------------------------

elif page == "new":
    st.subheader("Add New RFP")

    # --------------------------
    # Session state init
    # --------------------------
    st.session_state.setdefault("skill_items", [])  # List of {id, name, level}
    st.session_state.setdefault("language_items", [])  # List of {id, name, level}

    # --------------------------
    # Role & company information
    # --------------------------
    role = st.text_input("Role Title", key="role")
    company_name = st.text_input("Company Name", key="company_name")
    company_city = st.text_input("Localisation", key="company_city")

    # --------------------------
    # JOB DESCRIPTION + SCAN
    # --------------------------
    st.write("### Job Description")
    job_desc = st.text_area("Job Description (HTML allowed)", key="job_desc")

    if st.button("Scan skills"):
        skill_terms = load_skill_terms("skill_db_relax_20.json")
        extractor = create_extractor(skill_terms)
        extracted = extract_skills(job_desc, extractor)

        # Ajouter automatiquement les skills extraits à la liste avec des IDs simples
        st.session_state.skill_items = [
            {"id": i, "name": skill.strip(), "level": ""}
            for i, skill in enumerate(extracted)
            if skill.strip() != ""
        ]
        st.rerun()

    # -------------------------------------------------------------------
    # SKILLS SECTION
    # -------------------------------------------------------------------
    st.write("### Skills")
    
    st.session_state.setdefault("skill_items", [])
    
    for skill_item in st.session_state.skill_items:
        col1, col2, col3 = st.columns([4, 3, 1])
        
        item_id = skill_item["id"]
        skill_item["name"] = col1.text_input(
            f"Skill", 
            value=skill_item["name"], 
            key=f"skill_text_{item_id}"
        )
        
        level_list = ["", "Beginner", "Intermediate", "Advanced", "Expert"]
        level_idx = level_list.index(skill_item["level"]) if skill_item["level"] in level_list else 0
        
        skill_item["level"] = col2.selectbox(
            f"Level",
            level_list,
            index=level_idx,
            key=f"skill_level_select_{item_id}"
        )
        
        # Delete immediately when button is clicked
        if col3.button("-", key=f"delete_skill_btn_{item_id}"):
            st.session_state.skill_items = [s for s in st.session_state.skill_items if s["id"] != item_id]
            st.rerun()
    
    # ADD SKILL BUTTON
    if st.button("+ Add Skill", key="add_skill_btn"):
        next_id = max([s["id"] for s in st.session_state.skill_items], default=-1) + 1
        st.session_state.skill_items.append({
            "id": next_id,
            "name": "",
            "level": ""
        })
        st.rerun()

    # -------------------------------------------------------------------
    # LANGUAGES SECTION
    # -------------------------------------------------------------------
    st.write("### Languages")

    st.session_state.setdefault("language_items", [])

    for lang_item in st.session_state.language_items:
        col1, col2, col3 = st.columns([4, 3, 1])
        
        item_id = lang_item["id"]

        lang_item["name"] = col1.selectbox(
            f"Language",
            ["", "English", "French", "Dutch", "German", "Spanish"],
            index=["", "English", "French", "Dutch", "German", "Spanish"].index(lang_item["name"]) if lang_item["name"] in ["", "English", "French", "Dutch", "German", "Spanish"] else 0,
            key=f"lang_{item_id}",
        )

        lang_item["level"] = col2.selectbox(
            f"Level",
            ["", "NativeOrBilingual", "Fluent", "Professional", "Intermediate", "NiceToHave"],
            index=["", "NativeOrBilingual", "Fluent", "Professional", "Intermediate", "NiceToHave"].index(lang_item["level"]) if lang_item["level"] in ["", "NativeOrBilingual", "Fluent", "Professional", "Intermediate", "NiceToHave"] else 0,
            key=f"lang_level_{item_id}",
        )

        if col3.button("-", key=f"delete_lang_btn_{item_id}"):
            st.session_state.language_items = [l for l in st.session_state.language_items if l["id"] != item_id]
            st.rerun()

    if st.button("+ Add Language", key="add_lang_btn"):
        next_id = max([l["id"] for l in st.session_state.language_items], default=-1) + 1
        st.session_state.language_items.append({
            "id": next_id,
            "name": "",
            "level": ""
        })
        st.rerun()

    # -------------------------------------------------------------------
    # SAVE TO MONGODB
    # -------------------------------------------------------------------
    
    st.divider()

    if st.button("💾 Save RFP"):
        rfp_doc = {
            "job_id": str(uuid.uuid4()),
            "role": role,
            "company_name": company_name,
            "company_city": company_city,
            "job_description": job_desc,

            "skills": [
                {"name": s["name"].strip(), "level": s["level"]}
                for s in st.session_state.skill_items
                if s["name"].strip() != ""
            ],

            "languages": [
                {"name": l["name"], "level": l["level"]}
                for l in st.session_state.language_items
                if l["name"] != ""
            ]
        }

        result = collection.insert_one(rfp_doc)
        st.success(f"RFP saved! ID: {result.inserted_id}")

        # Reset the lists
        st.session_state.skill_items = []
        st.session_state.language_items = []

    # -------------------------------------------------------------------
    # BACK BUTTON
    # -------------------------------------------------------------------
    if st.button("⬅ Back"):
        go_to("list")

