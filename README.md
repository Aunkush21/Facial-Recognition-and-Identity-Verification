# Facial Recognition Based Student Attendance System

A minimalist, automated attendance management system that utilizes computer vision to identify students and record their attendance in real-time. Built with Python using OpenCV for facial recognition and Tkinter for a clean, user-friendly graphical interface.

---

## 📌 Features

* **Real-Time Face Detection & Recognition:** Uses optimized OpenCV pipelines to detect and identify registered student faces via webcam.
* **Automated Attendance Logging:** Instantly logs the student's name, ID, and exact timestamp into a backend CSV database upon successful recognition.
* **User-Friendly GUI:** A clean, minimalist desktop application interface built using Tkinter for smooth navigation and operation.
* **Student Registration:** Simple onboarding flow to capture student images, train the facial recognition model, and store student profiles.

---

## 🛠️ System Architecture

The system functions across three main layers:
1.  **Presentation Layer (GUI):** Tkinter-based window to manage student registration, launch the attendance camera, and view logs.
2.  **Recognition Core:** OpenCV pipelines responsible for video capture, image preprocessing, face detection, and feature matching.
3.  **Storage Layer:** Local file system storing trained dataset models and a structured CSV database for attendance logs.

---

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.x installed on your machine. You will need a functioning webcam for the live recognition feature.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/facial-recognition-attendance.git](https://github.com/yourusername/facial-recognition-attendance.git)
   cd facial-recognition-attendance
