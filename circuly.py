import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

CIRCULY_BASE = "https://api.circuly.io/api/2025-01"
CIRCULY_VERSION = "2025-01"

BOX_CATALOG = {
    # special=True → return path requires manual handling (no pending_return)
    "igel":          {"price": 29.99,  "special": True},
    "maus":          {"price": 29.99,  "special": True},
    "fuchs":         {"price": 29.99,  "special": True},
    "bär":           {"price": 29.99,  "special": True},
    "ente":          {"price": 29.99,  "special": True},
    "reh":           {"price": 29.99,  "special": True},
    "wildschwein":   {"price": 29.99,  "special": True},
    # special=False → return path uses set_end_date → pending_return
    "hase":          {"price": 69.99,  "special": False},
    "wolf":          {"price": 69.99,  "special": False},
    "eichhörnchen":  {"price": 69.99,  "special": False},
    "waschbär":      {"price": 69.99,  "special": False},
    "eule":          {"price": 69.99,  "special": False},
    "gravitrax":     {"price": 99.99,  "special": False},
    "tiptoi":        {"price": 99.99,  "special": False},
    "schleich":      {"price": 99.99,  "special": False},
    "safari":        {"price": 99.99,  "special": False},
    "brio":          {"price": 99.99,  "special": False},
    "connetix":      {"price": 99.99,  "special": False},
    "modu":          {"price": 169.99, "special": False},
}

# Umlaut-less aliases seen in some Circuly item names → canonical key
_BOX_ALIASES = {
    "eichhorn": "eichhörnchen",
    "waschbar": "waschbär",
}


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
    """Extract canonical box type keyword from Circuly item name.
    Checks aliases first (longest-first), then catalog keys (longest-first).
    Returns 'other' if no match found."""
    name_lower = item_name.lower()
    # Check aliases first — resolve to canonical key
    for alias in sorted(_BOX_ALIASES, key=len, reverse=True):
        if alias in name_lower:
            return _BOX_ALIASES[alias]
    # Check catalog keys
    for key in sorted(BOX_CATALOG, key=len, reverse=True):
        if key in name_lower:
            return key
    return "other"


def is_special_box(box_type: str) -> bool:
    """Special boxes: return choice → manual handling, no pending_return.
    Accepts both canonical keys ('reh') and raw Circuly item names ('[+15M] Reh Box')."""
    if box_type not in BOX_CATALOG:
        box_type = extract_box_type(box_type)
    return BOX_CATALOG.get(box_type, {}).get("special", False)


def get_price(box_type: str) -> float:
    """Return buyout price for a given box type key or raw Circuly item name.
    Accepts both canonical keys ('reh') and raw item names ('[+15M] Reh Box').
    Falls back to 49.99 for unknown/empty box types."""
    if box_type not in BOX_CATALOG:
        box_type = extract_box_type(box_type)
    return BOX_CATALOG.get(box_type, {}).get("price", 49.99)


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
