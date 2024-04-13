import cv2
import numpy as np
import pandas as pd
import datetime
import os
import sys

# Paths for files
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(current_dir, 'venv', 'templates', 'csv', 'student_details.csv')
attendance_folder = os.path.join(current_dir, 'attendance')
if not os.path.exists(attendance_folder):
    os.makedirs(attendance_folder)

date_today = datetime.datetime.now().strftime("%Y-%m-%d")

# Function to retrieve student details from the CSV file
def get_students_details():
    students_data =pd.read_csv(data_file_path, usecols=['Name','Roll No'])
    students_details_list = []

    for index, row in students_data.iterrows():
        name = row['Name'].lower()
        roll_no = row['Roll No']

        students_details_list.append({'name': name, 'roll_no': roll_no})

    return students_details_list

# Load existing attendance data and check status
def load_attendance_check_status(attendance_folder, date_today, students_details):
    """
    Load existing attendance data from a CSV file and check if it's already marked for today's date.

    Args:
    - attendance_folder (str): Path to the folder containing attendance CSV files.
    - date_today (str): Current date in 'YYYY-MM-DD' format.
    - students_details (list): List of dictionaries containing student details.

    Returns:
    - last_date (str or None): Last date for which attendance was marked, or None if no attendance data exists.
    - attendance_file_path (str): Path to the attendance CSV file.
    - attendance_marked (bool): True if attendance is already marked for any student, False otherwise.
    """
    attendance_file_path = os.path.join(attendance_folder, f'Attendance-{date_today}.csv')
    last_date = None
    attendance_marked = False
   
    # Load the existing attendance data if the file exists
    if os.path.exists(attendance_file_path):
        attendance_data = pd.read_csv(attendance_file_path)

        # Check if the DataFrame is not empty
        if not attendance_data.empty:
            last_date = attendance_data['date'].iloc[-1]

            if date_today == last_date:
                print("The attendance is already marked for today.")

                # Check if attendance is marked for any student with the provided rollno
                for student in students_details:
                    rollno_to_check = student['roll_no']  # Make sure the key is 'roll_no'
                    if rollno_to_check in attendance_data['rollno'].values:
                        print(f"Attendance is already marked for student with rollno {rollno_to_check} ({student['name']}).")
                        attendance_marked = True
                       
    return last_date, attendance_file_path, attendance_marked

# Get student details
student_details = get_students_details()

# Load existing attendance data and check status
last_date, attendance_file_path, attendance_marked = load_attendance_check_status(attendance_folder, date_today, student_details)

# If attendance is already marked for today's date or all students, exit the program
if last_date == date_today or attendance_marked:
    sys.exit()

# Function to create or load attendance data for the day
def get_attendance_data():
    attendance_file_path = os.path.join(attendance_folder, f'Attendance-{date_today}.csv')

    if os.path.exists(attendance_file_path):
        attendance_data = pd.read_csv(attendance_file_path)
    else:
        attendance_data = pd.DataFrame(columns=['date', 'name', 'rollno', 'total_recognized', 'status'])

    return attendance_data, attendance_file_path

# Get student details
students_details = get_students_details()

# Creating a list of images and class names
path = os.path.join(current_dir, 'venv', 'templates', 'images')
class_names = []
mylist = os.listdir(path)

# Appending class names
for cls in mylist:
    class_names.append(os.path.splitext(cls)[0])

print(class_names)

# Load the Haar cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Load or create attendance data
attendance_data, attendance_file_path = get_attendance_data()

# Opening webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Set the initial start time
start_time = datetime.datetime.now()
time_interval = 120 # Set the time interval in seconds (2 minutes)

# Dictionary to keep track of recognized students and their recognition time
recognized_students_info = {}

while True:
    recognized = False

    # Read a frame from the webcam
    success, img = cap.read()
   
    # Check if the frame is successfully read
    if not success:
        print("Failed to read a frame from the webcam.")
        continue  # Skip processing this frame
   
    # Convert the frame to grayscale for face detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Draw bounding boxes around detected faces and display names
    for (x, y, w, h), name in zip(faces, class_names):
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Calculate the position for displaying the name
        text_x, text_y = x, y - 10

        # Check if the student is already recognized
        if name not in recognized_students_info:
            recognized_students_info[name] = {
                'recognized_start_time': datetime.datetime.now(),
                'details': students_details[class_names.index(name)]
            }
            recognized = True

        # Display the name within the bounding box
        recognized_student = recognized_students_info.get(name)
        if recognized_student:
            student_details = recognized_student['details']
            student_name = student_details['name']
            cv2.putText(img, f"Detected: {student_name}", (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(img, "UNKNOWN", (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Display the frame with bounding boxes and names
    cv2.imshow('frame', img)

    # Introduce a small delay to reduce resource usage
    cv2.waitKey(100)

    # Check if the time interval has elapsed
    elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
    if elapsed_time >= time_interval:
        break  # Exit the loop after the specified time interval

# Calculate total recognition time for each recognized student after the loop
attendance_records = []
for student_name, info in recognized_students_info.items():
    student = info['details']
    total_time_recognized = (datetime.datetime.now() - info['recognized_start_time']).total_seconds()

    # Mark as Present if total recognized time is greater than 60 seconds, else mark as Absent
    status = 'Present' if total_time_recognized > 60 else 'Absent'

    new_data = {
        'date': date_today,
        'name': student['name'],
        'rollno': student['roll_no'],
        'total_recognized': total_time_recognized,
        'status': status
    }
    attendance_records.append(new_data)

# Create DataFrame from attendance records
new_attendance_df = pd.DataFrame(attendance_records)

# Concatenate the new attendance data with existing data (if any)
attendance_data = pd.concat([attendance_data, new_attendance_df], ignore_index=True)

# Save the attendance to the CSV file
attendance_data.to_csv(attendance_file_path, index=False)
print("Attendance marked.")

# Release the webcam and close the OpenCV windows
cap.release()
cv2.destroyAllWindows()
sys.exit()





