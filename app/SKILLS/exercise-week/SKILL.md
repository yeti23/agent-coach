---
name: exercise-week
description: Use this skill to validate personal user's activities for file exercise_week_WEEKNUMBER.csv
---

# Activity Skill

This skill ensures that all values conform to the schema of `exercise_week_WEEKNUMBER.csv`.


## Instructions

All values must conform to this list:

1. user_id
2. date: date of the day
3. duration: duration of the activity in minutes
4. activityName: Outdoor Bike, Indoor Bike, muscle building, Running
5. startTime: start date and time (YYYY-MM-DD HH:MM:SS or DD/MM/YYYY HH:MM:SS)
6. endTime: end date and time (YYYY-MM-DD HH:MM:SS or DD/MM/YYYY HH:MM:SS)
7. averageHeartRate: average heart rate during the activity
8. elevationGain: elevation gain in meters
9. distance: distance in meters
10. calories: calories burned during the activity
11. speed: average speed

For activity `muscle building`, values for distance, elevationGain, and speed are 0.0 or 0.