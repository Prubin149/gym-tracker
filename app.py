import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from pathlib import Path

st.set_page_config(page_title="Gym Tracker", page_icon="🏋️", layout="centered")

DATA_FILE = "gym_log.csv"


def load_data():
    if Path(DATA_FILE).exists():
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
        else:
            df = pd.DataFrame(columns=["Date", "Note"])
    else:
        df = pd.DataFrame(columns=["Date", "Note"])
    return df


def save_data(df):
    df_to_save = df.copy()
    if not df_to_save.empty:
        df_to_save["Date"] = pd.to_datetime(df_to_save["Date"]).dt.strftime("%Y-%m-%d")
    df_to_save.to_csv(DATA_FILE, index=False)


def calculate_current_streak(dates):
    if not dates:
        return 0

    date_set = set(dates)
    today = date.today()
    streak = 0
    current = today

    while current in date_set:
        streak += 1
        current = date.fromordinal(current.toordinal() - 1)

    return streak


def calculate_longest_streak(dates):
    if not dates:
        return 0

    sorted_dates = sorted(set(dates))
    longest = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i] - sorted_dates[i - 1]).days
        if diff == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def render_calendar(year, month, checked_dates):
    st.subheader("Calendar View")

    month_name = calendar.month_name[month]
    st.markdown(f"### {month_name} {year}")

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, wd in enumerate(weekdays):
        cols[i].markdown(f"**{wd}**")

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            is_current_month = day.month == month
            checked = day in checked_dates
            is_today = day == date.today()

            label = str(day.day)
            if checked:
                label = f"✅ {day.day}"
            elif is_today:
                label = f"📍 {day.day}"

            if is_current_month:
                cols[i].button(
                    label,
                    key=f"day_{day.isoformat()}",
                    use_container_width=True,
                    disabled=True,
                )
            else:
                cols[i].button(
                    " ",
                    key=f"blank_{day.isoformat()}",
                    use_container_width=True,
                    disabled=True,
                )


st.title("🏋️ Gym Tracker")

df = load_data()

st.markdown("Track your gym days, notes, and streaks.")

# Input section
with st.container():
    st.subheader("Add Gym Day")

    selected_date = st.date_input("Select Date", date.today())
    note = st.text_input("Workout Note (optional)", placeholder="Chest, legs, cardio...")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add / Update Gym Day", use_container_width=True):
            if selected_date in df["Date"].values:
                df.loc[df["Date"] == selected_date, "Note"] = note
                st.success("Gym day updated.")
            else:
                new_entry = pd.DataFrame([{"Date": selected_date, "Note": note}])
                df = pd.concat([df, new_entry], ignore_index=True)
                st.success("Gym day added.")
            save_data(df)
            st.rerun()

    with col2:
        if st.button("Remove Selected Day", use_container_width=True):
            if selected_date in df["Date"].values:
                df = df[df["Date"] != selected_date]
                save_data(df)
                st.success("Gym day removed.")
                st.rerun()
            else:
                st.warning("That day is not currently logged.")

# Stats
gym_dates = list(df["Date"]) if not df.empty else []
current_streak = calculate_current_streak(gym_dates)
longest_streak = calculate_longest_streak(gym_dates)

this_month_count = 0
if not df.empty:
    today = date.today()
    this_month_count = sum(
        1 for d in gym_dates if d.year == today.year and d.month == today.month
    )

col1, col2, col3 = st.columns(3)
col1.metric("🔥 Current Streak", current_streak)
col2.metric("🏆 Longest Streak", longest_streak)
col3.metric("📅 This Month", this_month_count)

st.divider()

# Calendar controls
today = date.today()
if "calendar_year" not in st.session_state:
    st.session_state.calendar_year = today.year
if "calendar_month" not in st.session_state:
    st.session_state.calendar_month = today.month

nav1, nav2, nav3 = st.columns(3)

with nav1:
    if st.button("⬅ Previous", use_container_width=True):
        if st.session_state.calendar_month == 1:
            st.session_state.calendar_month = 12
            st.session_state.calendar_year -= 1
        else:
            st.session_state.calendar_month -= 1
        st.rerun()

with nav2:
    if st.button("Today", use_container_width=True):
        st.session_state.calendar_year = today.year
        st.session_state.calendar_month = today.month
        st.rerun()

with nav3:
    if st.button("Next ➡", use_container_width=True):
        if st.session_state.calendar_month == 12:
            st.session_state.calendar_month = 1
            st.session_state.calendar_year += 1
        else:
            st.session_state.calendar_month += 1
        st.rerun()

checked_dates = set(gym_dates)
render_calendar(st.session_state.calendar_year, st.session_state.calendar_month, checked_dates)

st.divider()

# Recent entries
st.subheader("Recent Gym Days")

if df.empty:
    st.info("No gym days logged yet.")
else:
    df_display = df.copy()
    df_display["Date"] = pd.to_datetime(df_display["Date"]).dt.strftime("%Y-%m-%d")
    df_display = df_display.sort_values("Date", ascending=False)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
