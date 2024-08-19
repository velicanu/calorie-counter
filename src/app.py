import json
import os

import streamlit as st

from adders import dictionary_adder, init_sql, item_adder, nutrition_adder

SCRIPT_DIR = os.path.dirname(__file__)

valid_users = (
    json.load(open(os.path.join(SCRIPT_DIR, "users.json")))
    if os.path.exists(os.path.join(SCRIPT_DIR, "users.json"))
    else {}
)


def main():
    user = st.query_params.get("user")
    if user not in valid_users:
        st.error("Please provide a valid user")
        return "done"
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
