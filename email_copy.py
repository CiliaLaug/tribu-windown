# email_copy.py

SIGNATURE = """
<p>Alles Liebe,<br>
Cilia &amp; Daniela<br>
Dein Tribu-Team</p>
"""


def keep_confirmation() -> str:
    """Customer chose to keep their box — buyout processed."""
    return f"""
<p>Hallo,</p>
<p>wunderbar! Wir haben deine Zahlung erhalten – deine Box gehört jetzt dir. Du musst nichts weiter tun.</p>
<p>Vielen Dank für die schöne Zeit mit uns. Es war uns eine Freude! 🧡</p>
{SIGNATURE}
"""


def return_confirmation_standard() -> str:
    """Customer chose to return — standard box (pending_return path)."""
    return f"""
<p>Hallo,</p>
<p>alles klar! Wir kümmern uns um die Rücksendung und melden uns in Kürze mit allen Details per E-Mail.</p>
<p>Vielen Dank für die schöne Zeit mit uns. 🧡</p>
{SIGNATURE}
"""


def return_confirmation_special_box() -> str:
    """Customer chose to return — special box (igel/maus/fuchs/bär/ente/reh/wildschwein).
    We ask them to keep/donate/recycle instead."""
    return f"""
<p>Hallo,</p>
<p>wir haben deine Anfrage erhalten. Für Boxen wie deine ist es für uns tatsächlich am einfachsten, wenn du sie einfach behältst – gib sie gerne weiter, verschenke sie, spende sie oder recycle sie.</p>
<p>Wir kümmern uns darum, dein Abo auf unserer Seite zu beenden. Du musst nichts weiter tun. 🧡</p>
{SIGNATURE}
"""


def fallback_standard() -> str:
    """14-day non-responder — standard box. Subscription set to pending_return automatically."""
    return f"""
<p>Hallo,</p>
<p>da wir innerhalb von 14 Tagen keine Rückmeldung von dir erhalten haben, haben wir dein Abo automatisch beendet. Du erhältst in Kürze alle Details zur Rücksendung deiner Box per E-Mail.</p>
<p>Vielen Dank für die schöne Zeit mit uns. 🧡</p>
{SIGNATURE}
"""


def fallback_special_box() -> str:
    """14-day non-responder — special box. Same message as return_confirmation_special_box."""
    return return_confirmation_special_box()
