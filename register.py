import cv2
import os
import csv

def register_student(student_id, student_name):
    """Captures 20 face images of the student and saves registry data."""
    if not student_id or not student_name:
        return False, "Error: Both Student ID and Name are required!"

    dataset_path = f"dataset/{student_id}"
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    # Use Haar Cascade for fast initial face detection during registration
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cam = cv2.VideoCapture(0)

    count = 0
    while True:
        ret, img = cam.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            count += 1
            # Save the captured face region
            cv2.imwrite(f"{dataset_path}/{student_name}_{count}.jpg", gray[y:y+h, x:x+w])
            cv2.putText(img, f"Capturing: {count}/20", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('Registration - Capturing Faces', img)

        # Break if 'q' is pressed or 20 images are captured
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
        elif count >= 20:
            break

    cam.release()
    cv2.destroyAllWindows()

    # Log student info to the central registry
    csv_file = "student_data/students.csv"
    file_exists = os.path.isfile(csv_file)
    
    # Verify if student already exists to prevent duplicate rows
    if file_exists:
        with open(csv_file, mode='r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == student_id:
                    return True, f"Images updated for existing student: {student_name}"

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Student ID", "Student Name"])
        writer.writerow([student_id, student_name])

    return True, f"Successfully registered {student_name}!"