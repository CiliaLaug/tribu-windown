import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

CIRCULY_BASE = "https://api.circuly.io/api/2025-01"
CIRCULY_VERSION = "2025-01"

SPECIAL_BOX_TYPES = {"igel", "maus", "fuchs", "bär", "ente", "reh", "wildschwein"}
NON_SPECIAL_BOX_TYPES = {"hase", "wolf", "eichhörnchen", "waschbär", "eule",
                          "gravitrax", "tiptoi", "safari", "brio", "connetix", "modu"}
ALL_KNOWN_BOX_TYPES = SPECIAL_BOX_TYPES | NON_SPECIAL_BOX_TYPES


class CirculyError(Exception):
    pass


class CirculyNoSubscriptionError(CirculyError):
    """Raised when a customer has no active subscription."""
    pass


class CirculyMultipleSubscriptionsError(CirculyError):
    """Raised when a customer has more than one active subscription."""
    pass


def _auth() -> tuple:
    return os.environ.get("CIRCULY_USERNAME", ""), os.environ.get("CIRCULY_PASSWORD", "")


def _headers() -> dict:
    return {"Circuly-Version": CIRCULY_VERSION, "Content-Type": "application/json"}


def extract_box_type(item_name: str) -> str:
    """Extract box type from item name. Returns lowercase keyword or 'other'.
    Longest keyword matched first so 'waschbär' beats 'bär'."""
    name_lower = item_name.lower()
    for box in sorted(ALL_KNOWN_BOX_TYPES, key=len, reverse=True):
        if box in name_lower:
            return box
    return "other"


def is_special_box(box_type: str) -> bool:
    """Special boxes: return choice → manual handling, no pending_return."""
    return box_type in SPECIAL_BOX_TYPES


def get_active_subscription(customer_id: str) -> tuple:
    """
    Returns (subscription_id, box_type) for the single active subscription.
    Raises CirculyError if 0 or >1 active subscriptions found.
    """
    resp = requests.get(
        f"{CIRCULY_BASE}/subscriptions",
        params={"customer_id": customer_id, "status": "active"},
        auth=_auth(),
        headers=_headers(),
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])

    if len(data) == 0:
        raise CirculyNoSubscriptionError(f"0 active subscriptions found for {customer_id}")
    if len(data) > 1:
        raise CirculyMultipleSubscriptionsError(
            f"{len(data)} active subscriptions found for {customer_id}"
        )

    sub = data[0]
    sub_id = sub["id"]
    item_name = sub.get("item", {}).get("name", "")
    box_type = extract_box_type(item_name)
    return sub_id, box_type


def process_buyout(subscription_id: str) -> None:
    """
    Trigger process-buyout. Charges the customer's saved payment method
    at variant buyout prices and sets status to 'bought out'.
    Raises CirculyError on failure.
    """
    resp = requests.post(
        f"{CIRCULY_BASE}/css/subscriptions/{subscription_id}/process-buyout",
        json={},
        auth=_auth(),
        headers=_headers(),
    )
    if not resp.ok:
        msg = resp.json().get("message", resp.text) if resp.content else resp.reason
        raise CirculyError(f"process-buyout failed ({resp.status_code}): {msg}")
    body = resp.json()
    if "message" in body and "not allowed" in body["message"].lower():
        raise CirculyError(body["message"])


def set_end_date(subscription_id: str, end_date: str) -> None:
    """
    Set real_end_date on subscription → moves to pending_return.
    Used for non-special box return path.
    end_date: ISO date string e.g. '2026-05-07'
    Raises CirculyError on failure.
    """
    resp = requests.put(
        f"{CIRCULY_BASE}/subscriptions/{subscription_id}",
        json={"real_end_date": end_date},
        auth=_auth(),
        headers=_headers(),
    )
    if not resp.ok:
        msg = resp.json().get("message", resp.text) if resp.content else resp.reason
        raise CirculyError(f"set_end_date failed ({resp.status_code}): {msg}")
