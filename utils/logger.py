"""
Simple JSON Lines logger for CraneIQ.

Each verification event is written as one JSON object per line
to logs/events.jsonl.

This file is later consumed by the Streamlit dashboard.
"""

import json
import os
from datetime import datetime


class EventLogger:
    """
    Handles append only logging of verification events.
    """

    def __init__(self, log_path="logs/events.jsonl"):
        self.log_path = log_path

        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # Create empty log file if missing
        if not os.path.exists(self.log_path):
            open(self.log_path, "w").close()

    def log(
        self,
        gesture,
        confidence,
        operator_action,
        verification_state,
    ):
        """
        Write one verification event to the log file.
        """

        event = {
            "timestamp": datetime.now().isoformat(),
            "gesture": gesture,
            "confidence": round(float(confidence), 3)
            if confidence is not None
            else None,
            "operator_action": operator_action,
            "verification_state": verification_state,
        }

        with open(self.log_path, "a", encoding="utf-8") as file:
            json.dump(event, file)
            file.write("\n")

    def clear(self):
        """
        Clear the event log.
        Useful before starting a new demo.
        """

        open(self.log_path, "w").close()

    def read(self):
        """
        Read all logged events.

        Returns:
            list[dict]
        """

        events = []

        with open(self.log_path, "r", encoding="utf-8") as file:

            for line in file:

                line = line.strip()

                if line:
                    events.append(json.loads(line))

        return events

