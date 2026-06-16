import os
import tkinter as tk
from tkinter import ttk, messagebox
import register
import train
import recognize
import pandas as pd
from datetime import datetime

# --- Auto Directory Setup ---
def setup_folders():
    folders = ["student_data", "dataset", "encodings", "attendance"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
setup_folders()

# --- GUI Application ---
class AttendanceSystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Facial Recognition Attendance System")
        self.geometry("500x450")
        self.resizable(False, False)
        
        # Configure styles
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 11, 'bold'), padding=10)
        style.configure('TLabel', font=('Helvetica', 10))

        # Title Label
        title_label = tk.Label(self, text="Academic Attendance System", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="white", pady=15)
        title_label.pack(fill=tk.X)

        # Buttons Frame
        btn_frame = tk.Frame(self, pady=20)
        btn_frame.pack()

        btn_register = ttk.Button(btn_frame, text="1. Register Student", command=self.open_register_window, width=25)
        btn_register.grid(row=0, column=0, pady=10)

        btn_train = ttk.Button(btn_frame, text="2. Train Model", command=self.train_action, width=25)
        btn_train.grid(row=1, column=0, pady=10)

        btn_attendance = ttk.Button(btn_frame, text="3. Start Attendance", command=self.attendance_action, width=25)
        btn_attendance.grid(row=2, column=0, pady=10)

        btn_view = ttk.Button(btn_frame, text="4. View Today's Attendance", command=self.view_action, width=25)
        btn_view.grid(row=3, column=0, pady=10)

        btn_exit = ttk.Button(btn_frame, text="Exit", command=self.quit, width=25)
        btn_exit.grid(row=4, column=0, pady=10)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("System Ready.")
        status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Helvetica", 9), bg="#ecf0f1")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        self.status_var.set(f" Status: {message}")
        self.update_idletasks()

    def open_register_window(self):
        reg_win = tk.Toplevel(self)
        reg_win.title("Register New Student")
        reg_win.geometry("350x250")
        reg_win.resizable(False, False)

        tk.Label(reg_win, text="Student ID:").pack(pady=(20, 5))
        id_entry = ttk.Entry(reg_win, width=30)
        id_entry.pack()

        tk.Label(reg_win, text="Student Name:").pack(pady=(10, 5))
        name_entry = ttk.Entry(reg_win, width=30)
        name_entry.pack()

        def submit():
            sid = id_entry.get().strip()
            sname = name_entry.get().strip()
            self.set_status("Initializing camera for capture...")
            success, msg = register.register_student(sid, sname)
            if success:
                messagebox.showinfo("Success", msg)
                self.set_status("Capture complete.")
                reg_win.destroy()
            else:
                messagebox.showerror("Error", msg)
                self.set_status("Capture failed.")

        ttk.Button(reg_win, text="Capture Images", command=submit).pack(pady=20)

    def train_action(self):
        self.set_status("Training model... Please wait.")
        success, msg = train.train_model()
        if success:
            messagebox.showinfo("Success", msg)
            self.set_status("Model training complete.")
        else:
            messagebox.showerror("Error", msg)
            self.set_status("Model training failed.")

    def attendance_action(self):
        self.set_status("Starting camera for attendance. Press 'q' to stop.")
        success, msg = recognize.start_recognition()
        if success:
            messagebox.showinfo("Attendance Saved", msg)
            self.set_status("Attendance finalized.")
        else:
            messagebox.showerror("Error", msg)
            self.set_status("Attendance failed.")

    def view_action(self):
        date_today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"attendance/attendance_{date_today}.csv"
        
        if not os.path.exists(file_path):
            messagebox.showwarning("Not Found", "No attendance file found for today.")
            return
            
        try:
            df = pd.read_csv(file_path)
            # Calculate basic stats
            present_count = len(df[df['Status'] == 'Present'])
            total_count = len(df)
            percent = (present_count / total_count * 100) if total_count > 0 else 0
            
            messagebox.showinfo("Today's Summary", f"Date: {date_today}\nTotal Students: {total_count}\nPresent: {present_count}\nAttendance: {percent:.1f}%")
            # Automatically opens the CSV in Excel/Default system viewer
            os.startfile(os.path.abspath(file_path)) 
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")

if __name__ == "__main__":
    app = AttendanceSystem()
    app.mainloop()