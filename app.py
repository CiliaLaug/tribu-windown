import os
import hmac
import logging
from datetime import date, timedelta
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

import notion_log
import circuly
import freshdesk
import email_copy

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


def _process_end(customer: dict, is_fallback: bool = False) -> None:
    """
    Process 'return box' or 14-day fallback for a customer.
    Handles special box types (manual) vs standard (pending_return).
    """
    page_id = customer["page_id"]
    customer_id = customer["customer_id"]
    ticket_id = customer["freshdesk_ticket_id"]

    sub_id, box_type = circuly.get_active_subscription(customer_id)

    if circuly.is_special_box(box_type):
        # Special box: send keep/donate/recycle email, flag for manual handling
        body = email_copy.fallback_special_box() if is_fallback else email_copy.return_confirmation_special_box()
        freshdesk.reply_and_close(ticket_id, body)
        notion_log.mark_error(page_id, "manual_review_end_subscription")
    else:
        # Standard box: set end date → pending_return, send return email
        circuly.set_end_date(sub_id, date.today().isoformat())
        body = email_copy.fallback_standard() if is_fallback else email_copy.return_confirmation_standard()
        freshdesk.reply_and_close(ticket_id, body)
        status = "fallback" if is_fallback else "end"
        notion_log.mark_processed(page_id, status)


@app.route("/bye")
def landing():
    token = request.args.get("token", "")
    customer = notion_log.get_customer_by_token(token)

    if not customer:
        return render_template("error.html", message="Dieser Link ist leider nicht gültig.")

    if customer["status"] != "pending":
        return render_template(
            "error.html",
            message="Du hast bereits eine Entscheidung getroffen. Vielen Dank!"
        )

    return render_template("landing.html", token=token)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    choice = data.get("choice", "")

    if choice not in ("keep", "end"):
        return jsonify({"ok": False, "error": "invalid choice"}), 400

    customer = notion_log.get_customer_by_token(token)
    if not customer:
        return jsonify({"ok": False, "error": "invalid token"}), 400

    if customer["status"] != "pending":
        return jsonify({"ok": False, "error": "already processed"}), 400

    page_id = customer["page_id"]
    customer_id = customer["customer_id"]
    ticket_id = customer["freshdesk_ticket_id"]

    try:
        if choice == "keep":
            sub_id, _ = circuly.get_active_subscription(customer_id)
            circuly.process_buyout(sub_id)
            freshdesk.reply_and_close(ticket_id, email_copy.keep_confirmation())
            notion_log.mark_processed(page_id, "keep")
        else:
            _process_end(customer, is_fallback=False)

    except circuly.CirculyError as e:
        logging.error(f"Circuly error for {customer_id}: {e}")
        notion_log.mark_error(page_id, f"circuly_error: {e}")
        return jsonify({"ok": False, "error": "processing error"}), 500

    except freshdesk.FreshdeskError as e:
        logging.error(f"Freshdesk error for {customer_id} (Circuly already done): {e}")
        notion_log.mark_error(page_id, "circuly_done_freshdesk_failed")
        return jsonify({"ok": False, "error": "processing error"}), 500

    except Exception as e:
        logging.error(f"Unexpected error for {customer_id}: {e}")
        notion_log.mark_error(page_id, f"unexpected_error: {e}")
        return jsonify({"ok": False, "error": "processing error"}), 500

    return jsonify({"ok": True})


@app.route("/cron/fallback", methods=["POST"])
def cron_fallback():
    secret = request.headers.get("X-Cron-Secret", "")
    cron_secret = os.environ.get("CRON_SECRET", "")
    if not cron_secret or not hmac.compare_digest(secret, cron_secret):
        return jsonify({"error": "forbidden"}), 403

    cutoff = date.today() - timedelta(days=14)
    expired = notion_log.get_pending_expired(cutoff)
    logging.info(f"Cron: processing {len(expired)} expired customers")

    results = {"processed": 0, "errors": 0}
    for customer in expired:
        try:
            _process_end(customer, is_fallback=True)
            results["processed"] += 1
        except Exception as e:
            logging.error(f"Cron error for {customer['customer_id']}: {e}")
            notion_log.mark_error(customer["page_id"], f"cron_error: {e}")
            results["errors"] += 1

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=False)
