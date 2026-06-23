#!/usr/bin/env python3
"""Append a random float in [0, 1) to arm_commands.csv once per second."""

import csv
import random
import time
from datetime import datetime, timezone

CSV_PATH = "arm_commands.csv"
INTERVAL_SECONDS = 1.0
nowtime = time.time()


def main():
    with open(CSV_PATH, "w", newline="") as f:
        pass
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        # Write a header if the file is empty.
        if f.tell() == 0:
            writer.writerow(["timestamp", "command"])
            f.flush()

        while True:
            value = random.random()*0.8+0.2
            print(value)
            writer.writerow([time.time()-nowtime, value])
            f.flush()
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
