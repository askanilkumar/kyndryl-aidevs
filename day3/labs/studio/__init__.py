"""Agent Studio: one app that grows through the day (app_v1 -> app_v2 -> app_v3 -> studio_app)."""
import streamlit as st

from . import common

TABS = {
    "journey": ("0 · Journey", "tab_journey"),
    "arch": ("1 · Architecture", "tab_arch"),
    "think": ("2 · Think first", "tab_think"),
    "memory": ("3 · Memory", "tab_memory"),
    "run": ("4 · Agent run", "tab_run"),
    "safety": ("5 · Safety & evals", "tab_safety"),
    "failure": ("6 · Failure Lab", "tab_failure"),
    "lessons": ("7 · Lessons", "tab_lessons"),
}


def main(which, title="NetNova Agent Studio"):
    import importlib
    common.init(title)
    ctx = common.sidebar()
    labels = [TABS[k][0] for k in which]
    tabs = dict(zip(which, st.tabs(labels)))
    # Draw the architecture tab and the habit tiles LAST, so they show what the other tabs just did.
    for key in [k for k in which if k != "arch"] + [k for k in which if k == "arch"]:
        with tabs[key]:
            importlib.import_module(f"studio.{TABS[key][1]}").render(ctx)
    common.habits_panel(ctx["habit_box"])
