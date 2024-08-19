import streamlit as st
import os
from datetime import date, timedelta
import pandas as pd
import sqlite3
import plotly.express as px

today = date.today()
SCRIPT_DIR = os.path.dirname(__file__)


def change_state(key):
    st.session_state[key] = True


def get_nutrients(datadir, mass_filter="AND item != 'mass'"):
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df_nutrients = pd.read_sql(
            f"SELECT item FROM dictionary WHERE type = 'nutrient' {mass_filter}",
            conn,
        )
        nutrients = list(df_nutrients.to_dict()["item"].values())
    return nutrients


def get_foods(datadir):
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df_foods = pd.read_sql("SELECT item FROM dictionary WHERE type = 'food'", conn)
        foods = list(df_foods.to_dict()["item"].values())
    return foods


def item_adder(datadir):
    if "update_food" not in st.session_state:
        st.session_state["update_food"] = False
    cols = st.columns(2)
    with cols[0]:
        date_ = st.date_input("Date", value=today, max_value=today)
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df = pd.read_sql(
            "SELECT food, grams FROM food WHERE date = ? ", conn, params=(date_,)
        )
    foods = get_foods(datadir)
    with cols[0]:
        new_df = st.data_editor(
            df,
            use_container_width=False,
            column_config={
                "food": st.column_config.SelectboxColumn(
                    "food",
                    help="name of food",
                    options=foods,
                ),
                "grams": st.column_config.NumberColumn(
                    "grams",
                    help="grams of food",
                    min_value=0,
                    max_value=1000,
                ),
            },
            num_rows="dynamic",
            on_change=change_state,
            args=("update_food",),
            key=f"item_{datadir}",
        )
    if st.session_state["update_food"]:
        new_df = new_df.dropna()
        new_df["date"] = date_.isoformat()  # type: ignore
        with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
            conn.execute("DELETE FROM food WHERE date = ?", (date_,))
            new_df.to_sql("food", conn, index=False, if_exists="append")
        st.session_state["update_food"] = False
        st.rerun()

    # charts
    with cols[1]:
        dates = st.date_input(
            "Date range for charts",
            value=(today - timedelta(days=30), today),
            max_value=today,
        )
        nutrients = get_nutrients(datadir)
        nutrient = st.selectbox("Nutrition", options=nutrients)
    if len(dates) < 2:
        st.error("Please select a date range")
        return

    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df = pd.read_sql(
            """
            SELECT food.food as food, food.grams / n.value * nutrition.value as amount, food.date as date, nutrition.type as type
            FROM food
            JOIN nutrition ON food.food = nutrition.food
            JOIN nutrition n ON food.food = n.food WHERE n.type = 'mass' AND food.date >= ? AND food.date <= ? AND nutrition.type = ?
            """,
            conn,
            params=(dates[0], dates[1], nutrient),
        )
        df_sum = pd.read_sql(
            """
            SELECT sum(food.grams / n.value * nutrition.value) as amount, food.date as date, nutrition.type as type
            FROM food
            JOIN nutrition ON food.food = nutrition.food
            JOIN nutrition n ON food.food = n.food WHERE n.type = 'mass' AND food.date >= ? AND food.date <= ? AND nutrition.type = ? GROUP BY 2
            """,
            conn,
            params=(dates[0], dates[1], nutrient),
        )
        df_nutrient_sum = pd.read_sql(
            """
            SELECT sum(food.grams / n.value * nutrition.value) as amount, food.food as food
            FROM food
            JOIN nutrition ON food.food = nutrition.food
            JOIN nutrition n ON food.food = n.food WHERE n.type = 'mass' AND food.date >= ? AND food.date <= ? AND nutrition.type = ? GROUP BY 2
            """,
            conn,
            params=(dates[0], dates[1], nutrient),
        )
    fig_line = px.line(df_sum, x="date", y="amount", title=nutrient)
    fig_pie = px.pie(
        df_nutrient_sum,
        values="amount",
        names="food",
        title=f"{nutrient} from food",
    )
    cols = st.columns(2)
    with cols[0]:
        st.plotly_chart(fig_line, use_container_width=True)
    with cols[1]:
        st.plotly_chart(fig_pie, use_container_width=True)
    st.header(f"Daily {nutrient}")
    st.dataframe(df_sum)


def nutrition_adder(datadir):
    if "update_nutrition" not in st.session_state:
        st.session_state["update_nutrition"] = False
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df = pd.read_sql("SELECT * FROM nutrition", conn)
    foods = get_foods(datadir)
    nutrients = get_nutrients(datadir, mass_filter="")

    cols = st.columns(2)
    with cols[0]:
        st.header("Nutrition information")
        food = st.selectbox("Food", options=foods)
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df = pd.read_sql(
            "SELECT type, value FROM nutrition WHERE food = ?", conn, params=(food,)
        )
    new_df = st.data_editor(
        df,
        use_container_width=False,
        column_config={
            "type": st.column_config.SelectboxColumn(
                "type",
                help="type of nutrition",
                options=nutrients,
            ),
            "value": st.column_config.NumberColumn(
                "value",
                help="nutrient value",
                min_value=0.0,
            ),
        },
        num_rows="dynamic",
        on_change=change_state,
        args=("update_nutrition",),
        key=f"nutrition_{datadir}",
    )
    if st.session_state["update_nutrition"]:
        new_df = new_df.dropna()
        new_df["food"] = food
        with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
            conn.execute("DELETE FROM nutrition WHERE food = ?", (food,))
            new_df.to_sql("nutrition", conn, index=False, if_exists="append")
        st.session_state["update_nutrition"] = False
        st.rerun()


def add_dict_item(datadir, type_):
    if "update_dict_food" not in st.session_state:
        st.session_state["update_dict_food"] = False
    if "update_dict_nutrient" not in st.session_state:
        st.session_state["update_dict_nutrient"] = False
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        df = pd.read_sql(
            "SELECT item FROM dictionary WHERE type = ?", conn, params=(type_,)
        )
        st.session_state[f"dict_{type_}"] = df
    st.header(f"Add {type_.title()}")
    new_df = st.data_editor(
        df,
        use_container_width=False,
        column_config={
            "item": st.column_config.TextColumn(
                "item",
                help="name of item",
                required=True,
                validate=r"\w",
            )
        },
        num_rows="dynamic",
        on_change=change_state,
        args=(f"update_dict_{type_}",),
        key=f"dict_{type_}_{datadir}",
    )
    new_df = new_df.dropna()
    if st.session_state[f"update_dict_{type_}"]:
        new_df["type"] = type_
        with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
            conn.execute("DELETE FROM dictionary WHERE type = ?", (type_,))
            new_df.to_sql("dictionary", conn, index=False, if_exists="append")
        st.session_state[f"update_dict_{type_}"] = False
        st.rerun()


def dictionary_adder(datadir):
    cols = st.columns(2)
    with cols[0]:
        add_dict_item(datadir, "food")
    with cols[1]:
        add_dict_item(datadir, "nutrient")


def init_sql(datadir):
    with sqlite3.connect(os.path.join(datadir, "food.db")) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS food (
            food TEXT,
              grams REAL,
              date DATE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nutrition (
                food TEXT,
                  type TEXT,
                  value REAL
                );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dictionary (
                item TEXT,
                  type TEXT
                );
            """
        )
