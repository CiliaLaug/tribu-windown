# email_copy.py


def _signature() -> str:
    return """
<p style="margin-top: 24px;">
Alles Liebe,<br>
<strong>Cilia &amp; Daniela</strong><br>
<span style="color: #4f595f; font-size: 13px;">Dein Tribu-Team &nbsp;🧡</span>
</p>
"""


def _greeting(name: str) -> str:
    return f"<p>Hallo {name},</p>" if name else "<p>Hallo,</p>"


def keep_confirmation(name: str = "", price_str: str = "€49,99") -> str:
    """Customer chose to keep their box — buyout processed."""
    return f"""
{_greeting(name)}
<p>wie schön! Deine Box gehört jetzt offiziell dir. 🎉 Wir haben den Betrag von <strong>{price_str}</strong> erfolgreich verarbeitet – du musst nichts weiter tun.</p>
<p>Wir hoffen, dass sie noch lange Freude bringt. Von ganzem Herzen danke, dass du Teil der Tribu-Familie warst.</p>
{_signature()}
"""


def return_confirmation_standard(name: str = "") -> str:
    """Customer chose to return — standard box (pending_return path)."""
    return f"""
{_greeting(name)}
<p>alles klar! Du erhältst dein Rücksendeetikett in Kürze per E-Mail – bitte sende die Box innerhalb der nächsten 7 Tage zurück, um zusätzliche Kosten zu vermeiden.</p>
<p>Vielen Dank für die schöne Zeit mit uns. Es war uns wirklich eine Freude! 🧡</p>
{_signature()}
"""


def return_confirmation_special_box(name: str = "") -> str:
    """Customer chose to return — special box (igel/maus/fuchs/bär/ente/reh/wildschwein).
    We ask them to keep/donate/recycle instead."""
    return f"""
{_greeting(name)}
<p>wir haben deine Anfrage erhalten. Für Boxen wie deine ist es für uns am einfachsten, wenn du sie einfach behältst – gib sie gerne an Familie oder Freunde weiter, verschenke sie, spende sie oder recycle sie.</p>
<p>Wir kümmern uns darum, dein Abo auf unserer Seite zu beenden. Du musst nichts weiter tun. 🧡</p>
<p>Vielen Dank, dass du Teil der Tribu-Familie warst.</p>
{_signature()}
"""


def fallback_standard(name: str = "") -> str:
    """14-day non-responder — standard box. Subscription set to pending_return automatically."""
    return f"""
{_greeting(name)}
<p>da wir innerhalb von 14 Tagen keine Rückmeldung von dir erhalten haben, haben wir dein Abo automatisch beendet. Du erhältst dein Rücksendeetikett in Kürze per E-Mail – bitte sende die Box innerhalb der nächsten 7 Tage zurück, um zusätzliche Kosten zu vermeiden.</p>
<p>Bei Fragen sind wir jederzeit für dich da.</p>
{_signature()}
"""


def fallback_special_box(name: str = "") -> str:
    """14-day non-responder — special box. Acknowledges no response, asks to keep/donate/recycle."""
    return f"""
{_greeting(name)}
<p>da wir innerhalb von 14 Tagen keine Rückmeldung von dir erhalten haben, haben wir dein Abo automatisch beendet.</p>
<p>Für Boxen wie deine ist es für uns am einfachsten, wenn du sie einfach behältst – gib sie gerne an Familie oder Freunde weiter, verschenke sie, spende sie oder recycle sie. Du musst nichts weiter tun. 🧡</p>
<p>Vielen Dank, dass du Teil der Tribu-Familie warst.</p>
{_signature()}
"""
