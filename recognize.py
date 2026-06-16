import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
import attendance

def start_recognition():
    """Opens webcam, recognizes faces, and delegates attendance saving."""
    try:
        with open("encodings/encodings.pickle", "rb") as f:
            data = pickle.loads(f.read())
    except FileNotFoundError:
        return False, "Error: Model not trained yet! Please click 'Train Model'."

    students = attendance.load_students()
    present_session = {} # Dictionary to hold {student_id: time_of_arrival}

    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        # Resize frame to 1/4 size for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces in current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Calculate distance/confidence (Lower distance = higher match)
            face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
            
            name = "Unknown"
            student_id = "Unknown"
            confidence = 0

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                # Apply a strict threshold to avoid false positives (0.5 max distance)
                if face_distances[best_match_index] < 0.5:
                    student_id = data["ids"][best_match_index]
                    name = students.get(student_id, "Unknown")
                    confidence = round((1 - face_distances[best_match_index]) * 100)

            # Scale back up face locations since we processed a 1/4 sized frame
            top, right, bottom, left = face_location
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4

            # Green for known, Red for unknown
            color = (0, 255, 0) if student_id != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label = f"{name} ({confidence}%)" if student_id != "Unknown" else "Unknown"
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Log attendance temporarily in RAM if recognized
            if student_id != "Unknown" and student_id not in present_session:
                present_session[student_id] = datetime.now().strftime("%H:%M:%S")

        cv2.imshow("Live Attendance (Press 'q' to finalize)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

    # Delegate writing to CSV after closing the camera
    result_msg = attendance.finalize_attendance(present_session)
    return True, result_msg