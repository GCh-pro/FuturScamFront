import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from params import MONGO_URI, DB_NAME, COLLECTION_NAME

def go_to(page_name, **params):
    """Updates query params without using any deprecated API."""
    st.query_params.clear()
    st.query_params["page"] = page_name
    for k, v in params.items():
        st.query_params[k] = v
# -------------------------------------
# ----------- MONGODB SETUP ----------

@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


collection = get_collection()

query = st.query_params.to_dict()

page = query.get("page", "list")
doc_id = query.get("id")

# -------------------------------------
# ----------- SIDEBAR MENU ------------
# -------------------------------------

menu = st.sidebar.selectbox(
    "Navigation",
    ["RFP List", "Add New RFP"]
)

# Sidebar overrides the current page
if menu == "RFP List" and page != "detail":
    page = "list"
    go_to("list")

if menu == "Add New RFP":
    page = "new"
    go_to("new")
# -------------------------------------
# ----------- NAVIGATION --------------
# -------------------------------------

# Read current query params
query = st.query_params.to_dict()

page = query.get("page", "list")
doc_id = query.get("id")



# -------------------------------------
# ----------- PAGE: LIST --------------
# -------------------------------------

if page == "list":
    st.title("RFP List")

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
        st.title(doc.get("roleTitle", "RFP Detail"))

        st.subheader("Company")
        st.json(doc.get("company", {}))

        st.subheader("Conditions")
        st.json(doc.get("conditions", {}))

        st.subheader("Languages")
        st.json(doc.get("languages", []))

        st.subheader("Skills")
        st.json(doc.get("skills", []))

        st.subheader("Job Description")
        st.markdown(doc.get("job_desc", ""), unsafe_allow_html=True)

    st.divider()
    if st.button("⬅ Back to list"):
        go_to("list")

# -------------------------------------
# ----------- PAGE: NEW ---------------
# -------------------------------------

elif page == "new":
    st.title("Add New RFP")

    st.write("Fill the form to insert a new RFP document.")

    with st.form("rfp_form"):
        role = st.text_input("Role Title")
        company_name = st.text_input("Company Name")
        company_city = st.text_input("Company City")
        job_desc = st.text_area("Job Description (HTML allowed)")

        submitted = st.form_submit_button("Save")

        if submitted:
            new_doc = {
                "roleTitle": role,
                "company": {"name": company_name, "city": company_city},
                "job_desc": job_desc,
            }
            collection.insert_one(new_doc)
            st.success("RFP added!")
            go_to("list")

    if st.button("⬅ Back"):
        go_to("list")
