import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from params import MONGO_URI, DB_NAME, COLLECTION_NAME

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

    # ----- Config -----
    st.markdown("### Skills")
    skill_count = st.number_input(
        "Number of skills",
        min_value=1,
        max_value=50,
        step=1,
        value=1,
        key="skill_count",
    )

    st.markdown("### Languages")
    language_count = st.number_input(
        "Number of languages",
        min_value=0,
        max_value=20,
        step=1,
        value=1,
        key="language_count",
    )

    # ----- FORM -----
    with st.form("rfp_form"):
        role = st.text_input("Role Title")
        company_name = st.text_input("Company Name")
        company_city = st.text_input("Company City")

        job_desc = st.text_area(
            "Job Description (HTML allowed)",
            key="job_desc_input"
        )

        # -------- Skills --------
        st.markdown("### Skills")
        skill_names = []
        skill_levels = []

        for i in range(skill_count):
            cols = st.columns([3, 3])
            skill_names.append(
                cols[0].text_input(
                    f"Skill name {i+1}",
                    key=f"skill_name_{i}"
                )
            )
            skill_levels.append(
                cols[1].selectbox(
                    f"Seniority {i+1}",
                    ["", "Beginner", "Intermediate", "Advanced", "Expert"],
                    key=f"skill_level_{i}",
                )
            )

        # -------- Languages --------
        st.markdown("---")
        st.markdown("### Languages")
        lang_names = []
        lang_levels = []

        for i in range(language_count):
            cols = st.columns([3, 3])
            lang_names.append(
                cols[0].selectbox(
                    f"Language {i+1}",
                    ["", "English", "French", "Dutch", "German", "Spanish"],
                    key=f"lang_name_{i}",
                )
            )
            lang_levels.append(
                cols[1].selectbox(
                    f"Level {i+1}",
                    ["", "NativeOrBilingual", "Fluent", "Professional", "Intermediate", "NiceToHave"],
                    key=f"lang_level_{i}",
                )
            )

        submitted = st.form_submit_button("Save")


    st.divider()

    if st.button("⬅ Back"):
        go_to("list")
