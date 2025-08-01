def parse_email(email):
    """Parse email into user and domain parts."""
    # No validation - will crash on malformed input
    user, domain = email.split("@")
    return {"user": user, "domain": domain}


def format_email(user, domain):
    """Format user and domain into email string."""
    return f"{user}@{domain}"
