# tests/test_box_catalog.py
import pytest


@pytest.mark.parametrize("item_name, expected_key, expected_special, expected_price", [
    # Special boxes — €29,99, manual return handling
    ("Igel Box | annual",                "igel",          True,  29.99),
    ("Maus Box | monthly",               "maus",          True,  29.99),
    ("Fuchs Box | annual",               "fuchs",         True,  29.99),
    ("[+9M] Bär Box | annual",           "bär",           True,  29.99),
    ("Ente Box | monthly",               "ente",          True,  29.99),
    ("Reh Box | annual",                 "reh",           True,  29.99),
    ("Wildschwein Box | annual",         "wildschwein",   True,  29.99),
    # Non-special — €69,99, set_end_date → pending_return
    ("Hase Box | annual",                "hase",          False, 69.99),
    ("Wolf Box | annual",                "wolf",          False, 69.99),
    ("[+27M] Eichhörnchen Box | annual", "eichhörnchen",  False, 69.99),
    ("[+30M] Waschbär Box | annual",     "waschbär",      False, 69.99),
    ("Eule Box | monthly",               "eule",          False, 69.99),
    # Non-special — €99,99, set_end_date → pending_return
    ("GraviTrax Box | annual",           "gravitrax",     False, 99.99),
    ("TipToi Box | annual",              "tiptoi",        False, 99.99),
    ("Schleich Box | annual",            "schleich",      False, 99.99),
    ("Safari Box | annual",              "safari",        False, 99.99),
    ("BRIO Box | annual",                "brio",          False, 99.99),
    ("Connetix Box | annual",            "connetix",      False, 99.99),
    # Non-special — €169,99, set_end_date → pending_return
    ("[+3Y] MODU Box | annual",          "modu",          False, 169.99),
    # Aliases — umlaut-less Circuly item name variants
    ("[+27M] Eichhorn Box | annual",     "eichhörnchen",  False, 69.99),
    ("[+30M] Waschbar Box | annual",     "waschbär",      False, 69.99),
])
def test_box_classification(item_name, expected_key, expected_special, expected_price):
    from circuly import extract_box_type, is_special_box, get_price
    key = extract_box_type(item_name)
    assert key == expected_key, f"{item_name!r}: expected key {expected_key!r}, got {key!r}"
    assert is_special_box(key) == expected_special, f"{key!r}: expected special={expected_special}"
    assert get_price(key) == expected_price, f"{key!r}: expected price {expected_price}, got {get_price(key)}"
