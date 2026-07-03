"""
fix_csv.py  (one-off migration script — run this once)

Your gesture_data.csv currently has mixed row lengths:
  - old rows (recorded before session_id was added): 64 fields
      [63 landmark values, label]
  - new rows (recorded after the update): 65 fields
      [63 landmark values, label, session_id]

This script rewrites the CSV with a consistent 65-field format:
  - old rows get tagged with session_id = "legacy_session"
  - new rows keep their real session_id
  - a clean, correct header is written at the top

Run this once from the project root:
    python fix_csv.py

It backs up your original file to gesture_data_backup.csv first, just in case.
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