from datetime import datetime, timezone


def format_datetime_utc(value):
    if value is None:
        return "\u2014"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return value[:19] if len(value) > 19 else value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.strftime("%d-%m-%Y %H:%M UTC")
    return str(value)


def register_template_filters(env):
    env.filters["datetime_utc"] = format_datetime_utc
