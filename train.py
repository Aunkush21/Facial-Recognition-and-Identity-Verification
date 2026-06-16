import os
import cv2
import face_recognition
import pickle

def train_model():
    """Encodes captured images and saves them to a pickle file."""
    dataset_dir = "dataset"
    known_encodings = []
    known_ids = []

    if not os.path.exists(dataset_dir) or not os.listdir(dataset_dir):
        return False, "Error: Dataset folder is empty. Register students first."

    # Loop through all student folders
    for student_id in os.listdir(dataset_dir):
        student_folder = os.path.join(dataset_dir, student_id)
        if not os.path.isdir(student_folder):
            continue

        # Process each image
        for image_name in os.listdir(student_folder):
            image_path = os.path.join(student_folder, image_name)
            image = cv2.imread(image_path)
            if image is None:
                continue
                
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Extract face encodings
            encodings = face_recognition.face_encodings(rgb_image)
            if encodings:
                known_encodings.append(encodings[0])
                known_ids.append(student_id)

    if not known_encodings:
        return False, "Error: No valid faces found to train."

    # Serialize encodings securely
    data = {"encodings": known_encodings, "ids": known_ids}
    with open("encodings/encodings.pickle", "wb") as f:
        f.write(pickle.dumps(data))

    return True, "Model trained successfully! Ready for attendance."