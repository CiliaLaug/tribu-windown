# freshdesk.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

FRESHDESK_BASE = "https://tribu-box.freshdesk.com/api/v2"


class FreshdeskError(Exception):
    pass


def _auth() -> tuple[str, str]:
    return os.environ.get("FRESHDESK_API_KEY", ""), "X"


def reply_and_close(ticket_id: int, body_html: str) -> None:
    """
    Reply to an existing Freshdesk ticket with HTML body, then close it (status 5).
    Raises FreshdeskError if either call fails.
    """
    # Send reply
    reply_resp = requests.post(
        f"{FRESHDESK_BASE}/tickets/{ticket_id}/reply",
        auth=_auth(),
        json={"body": body_html},
    )
    if reply_resp.status_code != 201:
        raise FreshdeskError(f"Failed to reply to ticket {ticket_id}: {reply_resp.text}")

    # Close ticket
    close_resp = requests.put(
        f"{FRESHDESK_BASE}/tickets/{ticket_id}",
        auth=_auth(),
        json={"status": 5},
    )
    if close_resp.status_code != 200:
        raise FreshdeskError(f"Failed to close ticket {ticket_id}: {close_resp.text}")
