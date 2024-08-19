import streamlit as st
import os
from adders import item_adder, nutrition_adder, dictionary_adder, init_sql
import json

SCRIPT_DIR = os.path.dirname(__file__)
valid_users = json.load(open(os.path.join(SCRIPT_DIR, "users.json")))


def main():
    user = st.query_params.get("user")
    if user not in valid_users:
        st.error("Please provide a valid user")
        return "error"
    user_name = valid_users[user]
    st.header(f"Welcome, {user_name}!")
    datadir = os.path.join(SCRIPT_DIR, "data", user_name)
    os.makedirs(datadir, exist_ok=True)
    init_sql(datadir)
    st.title("Calorie counter")
    tab1, tab2, tab3 = st.tabs(["Food", "Nutrition", "Dictionary"])
    with tab1:
        item_adder(datadir)
    with tab2:
        nutrition_adder(datadir)
    with tab3:
        dictionary_adder(datadir)
    return "done"


if __name__ == "__main__":
    main()
