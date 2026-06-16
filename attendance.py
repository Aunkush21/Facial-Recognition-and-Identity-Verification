import os
import csv
from datetime import datetime
import pandas as pd

def load_students():
    """Loads registered students from CSV into a dictionary."""
    if not os.path.exists("student_data/students.csv"):
        return {}
    students = {}
    with open("student_data/students.csv", mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students[row["Student ID"]] = row["Student Name"]
    return students

def finalize_attendance(present_ids_with_time):
    """
    Saves attendance to a daily CSV file. 
    Marks missing students as Absent and prevents duplicate 'Present' entries.
    """
    date_today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"attendance/attendance_{date_today}.csv"
    students = load_students()

    if not students:
        return "Error: No registered students found."

    # Load existing attendance to preserve earlier 'Present' marks from the same day
    existing_data = {}
    if os.path.exists(file_path):
        with open(file_path, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row["Student ID"]] = row

    with open(file_path, mode='w', newline='') as f:
        fieldnames = ["Student ID", "Student Name", "Date", "Time", "Status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for st_id, name in students.items():
            # If student was detected in the current session
            if st_id in present_ids_with_time:
                writer.writerow({
                    "Student ID": st_id, "Student Name": name,
                    "Date": date_today, "Time": present_ids_with_time[st_id], "Status": "Present"
                })
            # If student was marked present in an earlier session today
            elif st_id in existing_data and existing_data[st_id]["Status"] == "Present":
                writer.writerow(existing_data[st_id])
            # If undetected entirely today
            else:
                writer.writerow({
                    "Student ID": st_id, "Student Name": name,
                    "Date": date_today, "Time": "-", "Status": "Absent"
                })
                
    return f"Attendance successfully saved to attendance_{date_today}.csv"