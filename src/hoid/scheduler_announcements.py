
"""Select varied, personalized HOID scheduler announcements."""

import json
import random
from pathlib import Path


DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "dialogue.json"
)


class AnnouncementSelector:
    def __init__(self, manifest_path=DEFAULT_MANIFEST):
        with Path(manifest_path).open(encoding="utf-8") as file:
            self.templates = json.load(file)

        self.last_selection = {}

    def select(self, kind, label=None):
        """Return a varied announcement for a timer or alarm."""
        if kind not in ("timer", "alarm"):
            raise ValueError(f"Unsupported job kind: {kind}")

        label = label.strip() if isinstance(label, str) else ""

        if kind == "timer":
            category = (
                "timer_finished"
                if label and label.casefold() != "timer"
                else "timer_finished_unlabeled"
            )
        else:
            category = "alarm_finished"

            if not label or label.casefold() == "alarm":
                label = "your scheduled alarm"

        templates = self.templates[category]

        previous = self.last_selection.get(category)
        choices = [
            index
            for index in range(len(templates))
            if index != previous
        ]

        if not choices:
            choices = list(range(len(templates)))

        index = random.choice(choices)
        self.last_selection[category] = index

        return templates[index].format(label=label)
