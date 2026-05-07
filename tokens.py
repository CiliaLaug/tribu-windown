import hmac
import hashlib


def generate_token(customer_id: str, secret: str) -> str:
    """Generate an HMAC-SHA256 token for a customer ID."""
    return hmac.new(
        secret.encode(),
        customer_id.encode(),
        hashlib.sha256
    ).hexdigest()
