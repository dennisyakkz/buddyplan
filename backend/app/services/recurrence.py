from datetime import date

DUTCH_DAYS = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
DUTCH_MONTHS = [
    "", "Januari", "Februari", "Maart", "April", "Mei", "Juni",
    "Juli", "Augustus", "September", "Oktober", "November", "December",
]
DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def monday_of_week(d: date) -> date:
    return d.fromordinal(d.toordinal() - d.weekday())


def week_dates(reference: date | None = None) -> list[date]:
    ref = reference or date.today()
    start = monday_of_week(ref)
    return [start.fromordinal(start.toordinal() + i) for i in range(7)]


def format_dutch_date(d: date) -> str:
    return f"{d.day} {DUTCH_MONTHS[d.month]}"


def format_dutch_day(d: date) -> str:
    return DUTCH_DAYS[d.weekday()]


def occurs_on_date(
    repeat_type: str,
    repeat_weekdays: list[int],
    anchor_date: date | None,
    end_date: date | None,
    target: date,
) -> bool:
    if not anchor_date:
        return False

    if repeat_type != "once" and target < anchor_date:
        return False

    if end_date and target > end_date:
        return False

    weekday = target.weekday()

    if repeat_type == "once":
        return target == anchor_date

    if repeat_type == "daily":
        return True

    if repeat_type == "weekly":
        return weekday == anchor_date.weekday()

    if repeat_type == "biweekly":
        days_diff = (target - anchor_date).days
        return days_diff >= 0 and days_diff % 14 == 0 and weekday == anchor_date.weekday()

    if repeat_type == "weekdays":
        return weekday in repeat_weekdays

    return False
