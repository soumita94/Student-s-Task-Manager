from __future__ import annotations

from datetime import datetime
import os
from typing import Any

import requests
import streamlit as st

DEFAULT_API_BASE = os.getenv("STM_API_BASE", "http://127.0.0.1:8000")
SORT_OPTIONS = ["priority", "deadline", "created"]
DEFAULT_API_TIMEOUT_SECONDS = 10
NLP_API_TIMEOUT_SECONDS = 35


def parse_iso_to_datetime_local(iso_str: str) -> datetime:
    value = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone()


def api_request(
    method: str,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = DEFAULT_API_TIMEOUT_SECONDS,
) -> requests.Response:
    base = st.session_state.api_base.rstrip("/")
    url = f"{base}{endpoint}"
    response = requests.request(
        method,
        url,
        params=params,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def fetch_tasks(sort_by: str, include_completed: bool) -> list[dict[str, Any]]:
    response = api_request(
        "GET",
        "/tasks",
        params={"sort_by": sort_by, "include_completed": include_completed},
    )
    return response.json()


def quick_add_task_nlp() -> None:
    st.subheader("Quick Add (NLP Command Box)")
    st.caption(
        'Example: "Add an assignment for algorithms due next Tuesday at 3 PM. It will take around 4 hours."'
    )
    with st.form("nlp_quick_add_form", clear_on_submit=True):
        command = st.text_area(
            "Task Command",
            height=120,
            placeholder="Describe the task naturally...",
        )
        submitted = st.form_submit_button("Quick Add Task")
        if not submitted:
            return
        if not command.strip():
            st.warning("Please enter a command.")
            return
        try:
            api_request(
                "POST",
                "/nlp/quick-add",
                payload={"text": command.strip()},
                timeout=NLP_API_TIMEOUT_SECONDS,
            )
            st.success("Task created from NLP command.")
            st.rerun()
        except requests.HTTPError as exc:
            st.error(f"NLP quick-add failed: {exc.response.text}")
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")


def render_task_row(task: dict[str, Any]) -> None:
    deadline_dt = parse_iso_to_datetime_local(task["deadline_at"])
    with st.container(border=True):
        st.markdown(f"### #{task['id']} - {task['title']}")
        st.write(task.get("description") or "_No description_")

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.write(f"**Kind:** {task['kind']}")
        meta_col2.write(f"**Importance:** {task['importance']}/10")
        meta_col3.write(f"**Priority Score:** {task['priority_score']:.2f}")
        st.caption(f"Deadline: {deadline_dt.strftime('%Y-%m-%d %H:%M %Z')}")

        action_col1, action_col2, action_col3 = st.columns(3)
        if action_col1.button(
            "Mark Done",
            key=f"done-{task['id']}",
            disabled=task["is_completed"],
            use_container_width=True,
        ):
            try:
                api_request("PATCH", f"/tasks/{task['id']}", payload={"is_completed": True})
                st.success(f"Task #{task['id']} marked complete.")
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Could not update task: {exc}")

        with action_col2.popover("Edit"):
            new_title = st.text_input("Title", value=task["title"], key=f"title-{task['id']}")
            new_description = st.text_area(
                "Description",
                value=task.get("description") or "",
                key=f"desc-{task['id']}",
            )
            new_kind = st.selectbox("Kind", ["rigid", "flexible"], index=0 if task["kind"] == "rigid" else 1, key=f"kind-{task['id']}")
            new_importance = st.slider(
                "Importance",
                1,
                10,
                int(task["importance"]),
                key=f"imp-{task['id']}",
            )
            existing_deadline = parse_iso_to_datetime_local(task["deadline_at"])
            new_deadline_date = st.date_input(
                "Deadline Date",
                value=existing_deadline.date(),
                key=f"date-{task['id']}",
            )
            new_deadline_time = st.time_input(
                "Deadline Time",
                value=existing_deadline.time().replace(tzinfo=None),
                key=f"time-{task['id']}",
            )
            current_estimate = task.get("estimated_minutes") or 0
            new_estimate = st.number_input(
                "Estimated Minutes",
                min_value=0,
                step=15,
                value=int(current_estimate),
                key=f"est-{task['id']}",
            )
            if st.button("Save", key=f"save-{task['id']}", use_container_width=True):
                payload = {
                    "title": new_title.strip(),
                    "description": new_description.strip() or None,
                    "kind": new_kind,
                    "deadline_at": datetime.combine(new_deadline_date, new_deadline_time).isoformat(),
                    "importance": int(new_importance),
                    "estimated_minutes": int(new_estimate) or None,
                }
                try:
                    api_request("PATCH", f"/tasks/{task['id']}", payload=payload)
                    st.success(f"Task #{task['id']} updated.")
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f"Could not save task: {exc}")

        if action_col3.button("Delete", key=f"delete-{task['id']}", use_container_width=True):
            try:
                api_request("DELETE", f"/tasks/{task['id']}")
                st.warning(f"Task #{task['id']} deleted.")
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Could not delete task: {exc}")


def main() -> None:
    st.set_page_config(page_title="Student Task Manager", page_icon=":calendar:", layout="wide")
    st.title("AI-Assisted Student Task Manager")
    st.caption("Streamlit frontend for your FastAPI backend.")

    if "api_base" not in st.session_state:
        st.session_state.api_base = DEFAULT_API_BASE

    with st.sidebar:
        st.header("Manual Task Entry")
        with st.form("manual_task_form", clear_on_submit=True):
            title = st.text_input("Title", placeholder="DBMS assignment")
            description = st.text_area("Description (optional)", height=80)
            kind = st.selectbox("Kind", ["rigid", "flexible"], index=1)
            deadline_date = st.date_input("Deadline Date")
            deadline_time = st.time_input("Deadline Time")
            importance = st.slider("Importance", min_value=1, max_value=10, value=5)
            category_weight = st.number_input(
                "Category Weight",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
            )
            estimated_minutes = st.number_input(
                "Estimated Minutes (optional)",
                min_value=0,
                value=0,
                step=15,
            )
            submitted_manual = st.form_submit_button("Add Task Manually", use_container_width=True)
            if submitted_manual:
                if not title.strip():
                    st.warning("Title is required.")
                else:
                    payload = {
                        "title": title.strip(),
                        "description": description.strip() or None,
                        "kind": kind,
                        "deadline_at": datetime.combine(deadline_date, deadline_time).isoformat(),
                        "category_weight": float(category_weight),
                        "importance": int(importance),
                        "estimated_minutes": int(estimated_minutes) or None,
                        "actual_time_taken": None,
                    }
                    try:
                        api_request("POST", "/tasks", payload=payload)
                        st.success("Task created manually.")
                        st.rerun()
                    except requests.HTTPError as exc:
                        st.error(f"Manual create failed: {exc.response.text}")
                    except requests.RequestException as exc:
                        st.error(f"API request failed: {exc}")

        st.divider()
        st.header("NLP Command Box")
        command = st.text_area(
            "Type your task naturally",
            height=140,
            placeholder="Add DBMS assignment due tomorrow 5 PM, estimate 2 hours",
        )
        if st.button("Quick Add via NLP", use_container_width=True):
            if not command.strip():
                st.warning("Please enter a command first.")
            else:
                try:
                    api_request(
                        "POST",
                        "/nlp/quick-add",
                        payload={"text": command.strip()},
                        timeout=NLP_API_TIMEOUT_SECONDS,
                    )
                    st.success("Task created from NLP command.")
                    st.rerun()
                except requests.HTTPError as exc:
                    st.error(f"NLP quick-add failed: {exc.response.text}")
                except requests.RequestException as exc:
                    st.error(
                        f"API request failed: {exc}. If this is a timeout, Gemini may be overloaded; please try again."
                    )

        st.divider()
        st.header("Settings")
        st.session_state.api_base = st.text_input("FastAPI Base URL", value=st.session_state.api_base)
        sort_by = st.selectbox("Sort Tasks By", SORT_OPTIONS, index=0)
        include_completed = st.checkbox("Include Completed Tasks", value=False)
        if st.button("Refresh Tasks", use_container_width=True):
            st.rerun()

    st.subheader("Task List")

    try:
        tasks = fetch_tasks(sort_by, include_completed)
    except requests.HTTPError as exc:
        st.error(f"Backend error: {exc.response.status_code} - {exc.response.text}")
        st.stop()
    except requests.RequestException as exc:
        st.error(f"Could not connect to FastAPI at {st.session_state.api_base}: {exc}")
        st.info("Start backend with: uvicorn app.main:app --reload")
        st.stop()

    if not tasks:
        st.info("No tasks yet. Create your first task above.")
        return

    open_count = sum(1 for task in tasks if not task["is_completed"])
    complete_count = len(tasks) - open_count
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Tasks", len(tasks))
    m2.metric("Open", open_count)
    m3.metric("Completed", complete_count)

    for task in tasks:
        render_task_row(task)


if __name__ == "__main__":
    main()

