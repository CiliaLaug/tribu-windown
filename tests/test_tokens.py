import pytest
from tokens import generate_token


def test_generate_token_is_deterministic():
    token = generate_token("cus_abc123", "mysecret")
    assert token == generate_token("cus_abc123", "mysecret")


def test_generate_token_differs_by_customer():
    t1 = generate_token("cus_aaa", "mysecret")
    t2 = generate_token("cus_bbb", "mysecret")
    assert t1 != t2


def test_generate_token_differs_by_secret():
    t1 = generate_token("cus_abc", "secret1")
    t2 = generate_token("cus_abc", "secret2")
    assert t1 != t2


def test_generate_token_is_hex_string():
    token = generate_token("cus_abc", "secret")
    assert isinstance(token, str)
    assert len(token) == 64  # SHA-256 = 32 bytes = 64 hex chars
