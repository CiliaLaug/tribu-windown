import os
from datetime import date
from typing import Optional
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()


def get_client() -> Client:
    return Client(auth=os.environ["NOTION_TOKEN"])


def _get_db_id() -> str:
    return os.environ.get("NOTION_DATABASE_ID", "")


def _text(prop) -> str:
    parts = prop.get("rich_text", [])
    return parts[0]["plain_text"] if parts else ""


def _parse_page(page: dict) -> dict:
    p = page["properties"]
    return {
        "page_id": page["id"],
        "customer_id": _text(p["customer_id"]),
        "email": p["email"].get("email") or "",
        "token": _text(p["token"]),
        "freshdesk_ticket_id": p["freshdesk_ticket_id"].get("number"),
        "sent_at": p["sent_at"]["date"]["start"] if p["sent_at"]["date"] else None,
        "status": p["status"]["select"]["name"] if p["status"]["select"] else None,
        "error_detail": _text(p["error_detail"]),
    }


def get_customer_by_token(token: str) -> Optional[dict]:
    client = get_client()
    result = client.databases.query(
        database_id=_get_db_id(),
        filter={"property": "token", "rich_text": {"equals": token}},
    )
    pages = result.get("results", [])
    if not pages:
        return None
    return _parse_page(pages[0])


def mark_processed(page_id: str, status: str) -> None:
    """Set status (keep/end/fallback) and processed_at=today."""
    client = get_client()
    client.pages.update(
        page_id=page_id,
        properties={
            "status": {"select": {"name": status}},
            "processed_at": {"date": {"start": date.today().isoformat()}},
        },
    )


def mark_error(page_id: str, error_detail: str) -> None:
    """Set status=error and populate error_detail. Row appears red in Notion."""
    client = get_client()
    client.pages.update(
        page_id=page_id,
        properties={
            "status": {"select": {"name": "error"}},
            "error_detail": {"rich_text": [{"text": {"content": error_detail}}]},
            "processed_at": {"date": {"start": date.today().isoformat()}},
        },
    )


def get_pending_expired(cutoff: date) -> list:
    """Return all pending rows where sent_at < cutoff (14-day fallback)."""
    client = get_client()
    results = []
    query_params = {
        "database_id": _get_db_id(),
        "filter": {
            "and": [
                {"property": "status", "select": {"equals": "pending"}},
                {"property": "sent_at", "date": {"before": cutoff.isoformat()}},
            ]
        },
    }
    while True:
        response = client.databases.query(**query_params)
        results.extend([_parse_page(p) for p in response["results"]])
        if not response.get("has_more"):
            break
        query_params["start_cursor"] = response["next_cursor"]
    return results
