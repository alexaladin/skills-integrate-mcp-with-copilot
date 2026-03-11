"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging
import os
import json
import secrets
import time
from pathlib import Path
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

logger = logging.getLogger(__name__)

ADMIN_SESSION_TTL_SECONDS = 60 * 60 * 8


class LoginRequest(BaseModel):
    username: str
    password: str

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


def load_teacher_credentials() -> dict[str, str]:
    """Load teacher credentials from teachers.json.

    Returns an empty dict and prints a warning if the file is absent or
    unreadable.  The example credentials file is intentionally never used as a
    fallback so that default/example passwords cannot be accepted in production.
    """
    teachers_path = current_dir / "teachers.json"

    if not teachers_path.exists():
        logger.warning(
            "teachers.json not found. "
            "Admin login is disabled until the file is created. "
            "See teachers.example.json for the expected format."
        )
        return {}

    try:
        with open(teachers_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load teachers.json: %s. Admin login is disabled.", exc)
        return {}

    teachers = raw_data.get("teachers", [])
    return {
        teacher["username"]: teacher["password"]
        for teacher in teachers
        if "username" in teacher and "password" in teacher
    }


teacher_credentials = load_teacher_credentials()

# In-memory admin sessions with expiry. This will reset on server restart.
active_admin_sessions: dict[str, dict[str, float | str]] = {}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def cleanup_expired_sessions() -> None:
    """Remove expired sessions to avoid unbounded growth."""
    now = time.time()
    expired_tokens = [
        token for token, session in active_admin_sessions.items()
        if float(session.get("expires_at", 0)) <= now
    ]
    for token in expired_tokens:
        active_admin_sessions.pop(token, None)


def require_admin_token(admin_token: str | None) -> str:
    """Validate admin token and return the associated username."""
    cleanup_expired_sessions()

    session = active_admin_sessions.get(admin_token) if admin_token else None
    if not admin_token or session is None:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required"
        )
    return str(session["username"])


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(payload: LoginRequest):
    """Authenticate a teacher and create an admin session token."""
    expected_password = teacher_credentials.get(payload.username)
    if expected_password is None or not secrets.compare_digest(payload.password, expected_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    cleanup_expired_sessions()

    token = secrets.token_urlsafe(24)
    active_admin_sessions[token] = {
        "username": payload.username,
        "expires_at": time.time() + ADMIN_SESSION_TTL_SECONDS,
    }
    return {"token": token, "username": payload.username}


@app.post("/auth/logout")
def logout(admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Invalidate the current admin session token."""
    require_admin_token(admin_token)
    active_admin_sessions.pop(admin_token, None)
    return {"message": "Logged out"}


@app.get("/auth/status")
def auth_status(admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Check whether an admin token is currently valid."""
    cleanup_expired_sessions()

    if not admin_token:
        return {"authenticated": False}

    session = active_admin_sessions.get(admin_token)
    if not session:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": session["username"]
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Sign up a student for an activity"""
    require_admin_token(admin_token)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Unregister a student from an activity"""
    require_admin_token(admin_token)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
