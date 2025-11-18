import streamlit as st

st.title("Test delete skill by button index")

# -------------------------
# Session state init
# -------------------------
if "skills" not in st.session_state:
    st.session_state.skills = ["Python", "SQL", "Docker", "AWS"]

if "to_delete" not in st.session_state:
    st.session_state.to_delete = None


# -------------------------
# Display skills with delete buttons
# -------------------------
st.subheader("Skill list")

for i, skill in enumerate(st.session_state.skills):
    col1, col2 = st.columns([6, 1])

    col1.write(f"**{i}. {skill}**")

    # Button with index
    if col2.button("🗑️", key=f"delete_btn_{i}"):
        st.session_state.to_delete = i


# DELETE AFTER LOOP (critical!)
if st.session_state.to_delete is not None:
    idx = st.session_state.to_delete
    del st.session_state.skills[idx]
    st.session_state.to_delete = None
    st.rerun()


# -------------------------
# Add new skill
# -------------------------
st.write("---")

if st.button("+ Add skill"):
    st.session_state.skills.append(f"New Skill {len(st.session_state.skills)+1}")
    st.rerun()
