# Box Catalog — Single Source of Truth Design

## Goal

Eliminate the risk of a box type being charged the wrong price or routed to the wrong return path by replacing two independently-maintained lists with a single `BOX_CATALOG` dict, backed by exhaustive tests covering every known box type.

## Problem

Two separate definitions must currently agree with each other but nothing enforces it:

- `SPECIAL_BOX_TYPES` / `NON_SPECIAL_BOX_TYPES` in `circuly.py` — controls the return path (manual handling vs. pending_return)
- `_PRICE_TIERS` in `app.py` — controls what the customer is charged

If one is edited and the other isn't, or a box type is accidentally in the wrong bucket, the wrong thing happens silently. Tests currently only cover ~6 of 18 known box types by example, leaving MODU, gravitrax, tiptoi, brio, wolf, eule, and others unverified.

## Architecture

### Single source of truth: `BOX_CATALOG` in `circuly.py`

Replace `SPECIAL_BOX_TYPES`, `NON_SPECIAL_BOX_TYPES`, `ALL_KNOWN_BOX_TYPES` with:

```python
BOX_CATALOG = {
    # special=True → return path requires manual handling (no pending_return)
    "igel":         {"price": 29.99,  "special": True},
    "maus":         {"price": 29.99,  "special": True},
    "fuchs":        {"price": 29.99,  "special": True},
    "bär":          {"price": 29.99,  "special": True},
    "ente":         {"price": 29.99,  "special": True},
    "reh":          {"price": 29.99,  "special": True},
    "wildschwein":  {"price": 29.99,  "special": True},
    # special=False → return path uses set_end_date → pending_return
    "hase":         {"price": 69.99,  "special": False},
    "wolf":         {"price": 69.99,  "special": False},
    "eichhörnchen": {"price": 69.99,  "special": False},
    "waschbär":     {"price": 69.99,  "special": False},
    "eule":         {"price": 69.99,  "special": False},
    "gravitrax":    {"price": 99.99,  "special": False},
    "tiptoi":       {"price": 99.99,  "special": False},
    "schleich":     {"price": 99.99,  "special": False},
    "safari":       {"price": 99.99,  "special": False},
    "brio":         {"price": 99.99,  "special": False},
    "connetix":     {"price": 99.99,  "special": False},
    "modu":         {"price": 169.99, "special": False},
}
```

### Aliases for umlaut-less Circuly item names

A small `_BOX_ALIASES` dict maps known umlaut-less variants to canonical keys, handled at extraction time so the catalog itself stays clean:

```python
_BOX_ALIASES = {
    "eichhorn": "eichhörnchen",
    "waschbar": "waschbär",
}
```

### Updated functions in `circuly.py`

**`extract_box_type(item_name)`** — unchanged logic, but uses `BOX_CATALOG.keys()` + `_BOX_ALIASES.keys()` for matching (longest-first). Aliases resolve to canonical key before returning.

**`is_special_box(box_type)`** — becomes:
```python
return BOX_CATALOG.get(box_type, {}).get("special", False)
```

**`get_price(box_type)`** — new function, moved here from `app.py`:
```python
return BOX_CATALOG.get(box_type, {}).get("price", 49.99)
```
Fallback €49,99 for unknown/empty box types (unchanged behaviour).

### Changes to `app.py`

- Remove `_PRICE_TIERS` list and `get_price()` function entirely
- Import and call `circuly.get_price(box_type)` instead
- `format_price()` stays in `app.py` (presentation concern, not classification)

## Tests

File: `tests/test_box_catalog.py`

One parametrized test covering all 19 canonical box types + 2 aliases:

```python
@pytest.mark.parametrize("item_name, expected_key, expected_special, expected_price", [
    # Special boxes — €29,99, manual return
    ("Igel Box | annual",              "igel",         True,  29.99),
    ("Maus Box | monthly",             "maus",         True,  29.99),
    ("Fuchs Box | annual",             "fuchs",        True,  29.99),
    ("[+9M] Bär Box | annual",         "bär",          True,  29.99),
    ("Ente Box | monthly",             "ente",         True,  29.99),
    ("Reh Box | annual",               "reh",          True,  29.99),
    ("Wildschwein Box | annual",       "wildschwein",  True,  29.99),
    # Non-special — €69,99, pending_return
    ("Hase Box | annual",              "hase",         False, 69.99),
    ("Wolf Box | annual",              "wolf",         False, 69.99),
    ("[+27M] Eichhörnchen Box | annual","eichhörnchen",False, 69.99),
    ("[+30M] Waschbär Box | annual",   "waschbär",     False, 69.99),
    ("Eule Box | monthly",             "eule",         False, 69.99),
    # Non-special — €99,99, pending_return
    ("GraviTrax Box | annual",         "gravitrax",    False, 99.99),
    ("TipToi Box | annual",            "tiptoi",       False, 99.99),
    ("Schleich Box | annual",          "schleich",     False, 99.99),
    ("Safari Box | annual",            "safari",       False, 99.99),
    ("BRIO Box | annual",              "brio",         False, 99.99),
    ("Connetix Box | annual",          "connetix",     False, 99.99),
    # Non-special — €169,99, pending_return
    ("[+3Y] MODU Box | annual",        "modu",         False, 169.99),
    # Aliases (umlaut-less Circuly variants)
    ("[+27M] Eichhorn Box | annual",   "eichhörnchen", False, 69.99),
    ("[+30M] Waschbar Box | annual",   "waschbär",     False, 69.99),
])
def test_box_classification(item_name, expected_key, expected_special, expected_price):
    from circuly import extract_box_type, is_special_box, get_price
    key = extract_box_type(item_name)
    assert key == expected_key
    assert is_special_box(key) == expected_special
    assert get_price(key) == expected_price
```

Existing spot-check tests in `test_circuly.py` remain and continue to pass.

## Files Changed

| File | Change |
|------|--------|
| `circuly.py` | Add `BOX_CATALOG`, `_BOX_ALIASES`; update `extract_box_type`, `is_special_box`; add `get_price` |
| `app.py` | Remove `_PRICE_TIERS`, `get_price`; call `circuly.get_price()` instead |
| `tests/test_box_catalog.py` | New file — exhaustive parametrized test table |

## What This Eliminates

- Price and special classification can never disagree — one dict, two readers
- Every known box type is explicitly asserted in tests — no silent fallbacks
- Aliases for umlaut-less names are handled at extraction, not scattered across two files
