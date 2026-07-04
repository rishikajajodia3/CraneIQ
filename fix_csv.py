"""
fix_csv.py (one-time migration utility)

This script updates gesture_data.csv so every row follows the same format.

Supported formats:
  • Legacy rows (64 columns):
      [63 landmark values, label]
  • Current rows (65 columns):
      [63 landmark values, label, session_id]

During migration:
  • Legacy rows are assigned session_id = "legacy_session".
  • Existing session IDs are preserved.
  • A fresh header is written to the output CSV.

The original dataset is backed up as gesture_data_backup.csv before any
changes are made.

Run from the project root:
    python fix_csv.py
"""

import csv
import os
import shutil

CSV_PATH = "gesture_data.csv"
BACKUP_PATH = "gesture_data_backup.csv"

NUM_LANDMARKS = 21
LANDMARK_COLS = [f"lm{i}_{axis}" for i in range(NUM_LANDMARKS) for axis in ("x", "y", "z")]
NEW_HEADER = LANDMARK_COLS + ["label", "session_id"]


def main():
    if not os.path.isfile(CSV_PATH):
        print(f"Could not find {CSV_PATH} in the current folder. Run this from your project root.")
        return

    shutil.copy(CSV_PATH, BACKUP_PATH)
    print(f"Backed up original file to {BACKUP_PATH}")

    fixed_rows = []
    skipped = 0

    with open(CSV_PATH, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # discard old header, we'll write a fresh one

        for row in reader:
            if len(row) == 64:
                # old-format row: [63 landmarks, label] -> tag as legacy
                fixed_rows.append(row + ["legacy_session"])
            elif len(row) == 65:
                # already has session_id, keep as-is
                fixed_rows.append(row)
            else:
                # unexpected row length, skip it rather than guess
                skipped += 1

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(NEW_HEADER)
        writer.writerows(fixed_rows)

    print(f"Rewrote {CSV_PATH}: {len(fixed_rows)} rows kept, {skipped} malformed rows skipped.")
    print("You can now run: python -m scripts.3_train_model")


if __name__ == "__main__":
    main()
