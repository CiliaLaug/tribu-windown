# Box Catalog — Single Source of Truth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace two independently-maintained box type lists with a single `BOX_CATALOG` dict so price and return-path classification can never disagree, backed by exhaustive tests for all 19 box types.

**Architecture:** `BOX_CATALOG` lives in `circuly.py` and is the only place box types, prices, and special flags are defined. `is_special_box()` and a new `get_price()` both read from it. `app.py` drops its own `_PRICE_TIERS`/`get_price()` and delegates to `circuly.get_price()`. A new test file covers every known box type end-to-end.

**Tech Stack:** Python 3.9, Flask, pytest

---

## File Map

| File | What changes |
|------|-------------|
| `circuly.py` | Replace `SPECIAL_BOX_TYPES`/`NON_SPECIAL_BOX_TYPES`/`ALL_KNOWN_BOX_TYPES` with `BOX_CATALOG` + `_BOX_ALIASES`; update `extract_box_type`, `is_special_box`; add `get_price` |
| `app.py` | Delete `_PRICE_TIERS` and `get_price()`; call `circuly.get_price()` in their place |
| `tests/test_box_catalog.py` | New file — exhaustive parametrized test for all 19 box types + 2 aliases |
| `tests/test_circuly.py` | No changes needed — existing spot-check tests still pass |

---

## Task 1: Add BOX_CATALOG and _BOX_ALIASES to circuly.py

**Files:**
- Modify: `circuly.py` (lines 11–14 — the three set definitions)

- [ ] **Step 1: Write the failing test**

Create `tests/test_box_catalog.py` with the full parametrized table. This file tests `get_price` which doesn't exist yet — so it will fail on import.

```python
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
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd tribu-winddown-landing
python3 -m pytest tests/test_box_catalog.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'get_price' from 'circuly'`

- [ ] **Step 3: Replace the three set definitions with BOX_CATALOG + _BOX_ALIASES in circuly.py**

Remove lines 11–14:
```python
SPECIAL_BOX_TYPES = {"igel", "maus", "fuchs", "bär", "ente", "reh", "wildschwein"}
NON_SPECIAL_BOX_TYPES = {"hase", "wolf", "eichhörnchen", "waschbär", "eule",
                          "gravitrax", "tiptoi", "safari", "brio", "connetix", "modu"}
ALL_KNOWN_BOX_TYPES = SPECIAL_BOX_TYPES | NON_SPECIAL_BOX_TYPES
```

Replace with:
```python
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
```

- [ ] **Step 4: Update extract_box_type to use BOX_CATALOG + _BOX_ALIASES**

Replace the existing `extract_box_type` function:
```python
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
```

- [ ] **Step 5: Update is_special_box to read from BOX_CATALOG**

Replace:
```python
def is_special_box(box_type: str) -> bool:
    """Special boxes: return choice → manual handling, no pending_return."""
    return box_type in SPECIAL_BOX_TYPES
```

With:
```python
def is_special_box(box_type: str) -> bool:
    """Special boxes: return choice → manual handling, no pending_return."""
    return BOX_CATALOG.get(box_type, {}).get("special", False)
```

- [ ] **Step 6: Add get_price to circuly.py**

Add immediately after `is_special_box`:
```python
def get_price(box_type: str) -> float:
    """Return buyout price for a given canonical box type key.
    Falls back to 49.99 for unknown/empty box types."""
    return BOX_CATALOG.get(box_type, {}).get("price", 49.99)
```

- [ ] **Step 7: Run the new tests — all 21 cases must pass**

```bash
python3 -m pytest tests/test_box_catalog.py -v
```

Expected: `21 passed`

- [ ] **Step 8: Run the full test suite — all existing tests must still pass**

```bash
python3 -m pytest tests/ -q
```

Expected: `56 passed` (35 existing + 21 new)

- [ ] **Step 9: Commit**

```bash
git add circuly.py tests/test_box_catalog.py
git commit -m "feat: replace box type sets with BOX_CATALOG single source of truth

- BOX_CATALOG maps each box type to price + special flag
- _BOX_ALIASES handles umlaut-less Circuly item name variants
- extract_box_type and is_special_box read from BOX_CATALOG
- New get_price() reads from BOX_CATALOG (will replace app.py's _PRICE_TIERS)
- 21-case exhaustive test covers every known box type"
```

---

## Task 2: Remove _PRICE_TIERS from app.py, delegate to circuly.get_price()

**Files:**
- Modify: `app.py` (lines 20–45 — `_PRICE_TIERS` and `get_price()`)

- [ ] **Step 1: Delete _PRICE_TIERS and get_price() from app.py**

Remove these lines entirely (lines 18–45, including the comment header):
```python
# ── Price tiers ───────────────────────────────────────────────────────────────

_PRICE_TIERS = [
    (29.99,  ["igel", "maus", "fuchs", "bär", "ente", "reh", "wildschwein"]),
    (69.99,  ["hase", "wolf", "eichhörnchen", "eichhorn", "waschbär", "waschbar", "eule"]),
    (99.99,  ["gravitrax", "tiptoi", "schleich", "safari", "brio", "connetix"]),
    (169.99, ["modu"]),
]


def get_price(box_type: str) -> float:
    """Return buyout price for a given box_type string (matched by keyword).
    Longer keywords are checked first so 'waschbär' beats 'bär'."""
    bt = box_type.lower()
    candidates = sorted(
        ((kw, price) for price, keywords in _PRICE_TIERS for kw in keywords),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    for kw, price in candidates:
        if kw in bt:
            return price
    return 49.99  # fallback for unknown box types
```

- [ ] **Step 2: Replace all calls to get_price() with circuly.get_price() in app.py**

There are two call sites. Find them with:
```bash
grep -n "get_price" app.py
```

Replace each occurrence of `get_price(` with `circuly.get_price(`. The calls are:
- In the landing route: `price = get_price(box_type)` → `price = circuly.get_price(box_type)`
- In the submit route: `price_str = format_price(get_price(box_type))` → `price_str = format_price(circuly.get_price(box_type))`

`format_price()` stays in `app.py` — it's a display concern, not classification.

- [ ] **Step 3: Run the full test suite**

```bash
python3 -m pytest tests/ -q
```

Expected: `56 passed`

If any test in `test_app.py` fails with `NameError: name 'get_price' is not defined`, it's mocking the old local `get_price`. Check `tests/test_app.py` for any `patch("app.get_price", ...)` calls and update them to `patch("circuly.get_price", ...)` if present.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "refactor: remove _PRICE_TIERS from app.py, delegate to circuly.get_price()

Price classification now has a single source of truth in BOX_CATALOG.
app.py only handles formatting (format_price), not classification."
```

---

## Task 3: Push and verify on Render

- [ ] **Step 1: Push to GitHub**

```bash
git push
```

- [ ] **Step 2: Trigger manual deploy on Render**

Go to https://dashboard.render.com → tribu-winddown-landing → Manual Deploy → Deploy latest commit.

Wait ~60 seconds for the build to complete.

- [ ] **Step 3: Smoke-test the live landing page**

Open: `https://tschuss.tribu-box.com/?token=<any valid pending token>`

Confirm the correct price is shown for the box type in that Notion row. Use the Notion database to find a pending customer and their expected price.

- [ ] **Step 4: Done**

All 56 tests pass locally. BOX_CATALOG is the single source of truth. `_PRICE_TIERS` and the old `get_price()` in app.py are gone.
