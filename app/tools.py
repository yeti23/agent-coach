# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for accessing personal health and activity data."""

import csv
import glob
import os

# Resolve personal-data directory dynamically relative to this file
_PERSONAL_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)


def get_resting_health_summary() -> list[dict]:
    """Retrieve the user's daily resting health summary metrics.

    This includes weight, height, age, resting heart rate, heart rate
    variability (HRV), daily steps, and detailed sleep phase durations
    (REM, deep, light sleep, total sleep minutes, bed time, wake up time).

    Returns:
        A list of dictionaries, where each dictionary represents one day of resting health metrics.
    """
    summary_path = os.path.join(_PERSONAL_DATA_DIR, "user_1_summary.csv")
    if not os.path.exists(summary_path):
        return [{"error": f"Health summary data file not found at {summary_path}"}]

    data = []
    try:
        with open(summary_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                # Filter empty rows and ensure user_id is present
                if row.get("user_id"):
                    data.append(dict(row))
    except Exception as e:
        return [{"error": f"Failed to read health summary data: {e}"}]

    return data


def get_exercise_activities() -> list[dict]:
    """Retrieve the user's logged physical exercises and workout activities.

    This includes exercise name (e.g. Outdoor Bike, muscle building), activity
    date, duration (minutes), average heart rate, elevation gain, distance,
    speed, and calories burned.

    Returns:
        A list of dictionaries, where each dictionary represents one logged exercise session.
    """
    data = []
    try:
        # Find all exercise_week_*.csv files in the personal-data directory
        csv_pattern = os.path.join(_PERSONAL_DATA_DIR, "exercise_week_*.csv")
        csv_files = glob.glob(csv_pattern)

        if not csv_files:
            return [{"error": f"No exercise activity files found in {_PERSONAL_DATA_DIR}"}]

        for file_path in sorted(csv_files):
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    if row.get("user_id"):
                        data.append(dict(row))
    except Exception as e:
        return [{"error": f"Failed to read exercise activity data: {e}"}]

    return data
