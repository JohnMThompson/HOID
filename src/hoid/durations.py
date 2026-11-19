"""Conservative parsing of spoken timer durations."""

import re

_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3,
    "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}

_NUMBER_PATTERN = (
    r"(?:\d+|"
    + "|".join(_NUMBERS)
    + r")(?:[ -](?:one|two|three|four|five|six|seven|eight|nine))?"
)

_COMPONENT = re.compile(
    rf"(?P<number>{_NUMBER_PATTERN}) "
    r"(?P<unit>hours?|minutes?|seconds?)"
)

_MULTIPLIERS = {
    "hour": 3600,
    "minute": 60,
    "second": 1,
}


def _parse_number(text: str) -> int | None:
    if text.isdigit():
        return int(text)

    if text in _NUMBERS:
        return _NUMBERS[text]

    parts = re.split(r"[ -]", text)
    if (
        len(parts) == 2
        and parts[0] in _NUMBERS
        and parts[1] in _NUMBERS
        and _NUMBERS[parts[0]] >= 20
        and _NUMBERS[parts[0]] % 10 == 0
        and 1 <= _NUMBERS[parts[1]] <= 9
    ):
        return _NUMBERS[parts[0]] + _NUMBERS[parts[1]]

    return None


def parse_duration(text: str) -> int | None:
    """Parse a complete duration, returning seconds or None."""
    remaining = text.strip().lower()
    total = 0
    seen_units = set()

    while remaining:
        match = _COMPONENT.match(remaining)
        if match is None:
            return None

        number = _parse_number(match.group("number"))
        unit = match.group("unit").rstrip("s")

        if number is None or unit in seen_units:
            return None

        seen_units.add(unit)
        total += number * _MULTIPLIERS[unit]
        remaining = remaining[match.end():]

        if remaining:
            separator = re.match(r"(?: and | )", remaining)
            if separator is None:
                return None
            remaining = remaining[separator.end():]

    return total if 1 <= total <= 86400 else None
