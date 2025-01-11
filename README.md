# UBC Class Schedule to Calendar

Check out the project live here: [**UBC Class Schedule to Calendar**](https://schedule2calendar.pythonanywhere.com)


This project allows UBC students to seamlessly convert their class schedules into calendar events with full details, including the class location and the option to set notifications to remind them when to leave for class. This tool is especially helpful for those who find it difficult to navigate the campus, and it automates the process of tracking your classes while also including useful location data for easy navigation.

<p align="center">
  <img src="/images/Screenshot2.png" alt="Schedule2Calendar" width="800"/>
</p>



## Motivation

As a student at UBC, I found it frustrating when I first arrived, not knowing how to navigate the campus and how far my next class might be. I often had trouble finding classrooms, and this led to unnecessary stress. With this tool, I wanted to create a solution that provides all the necessary information—class times, locations, and reminders—directly in your calendar.

Now, you can simply upload your class schedule, and the application will generate a `.ics` calendar file that includes all the relevant details, so you don't have to worry about finding your classes again. It even lets you set notifications to remind you when to leave based on the time it takes to walk between buildings!

## Features

- **Class Schedule to Calendar**: Convert your class schedule into calendar events with full details.
- **Location and Address**: Automatically adds the address of your classrooms and provides a full location for easy navigation.
- **Time to Leave Notifications**: Set reminders to alert you when it's time to leave for your next class based on your location.
- **ICS File Export**: Export the schedule directly into an ICS file that can be imported into your preferred calendar application (Google Calendar, Apple Calendar, etc.).

## How It Works

1. Download your class schedule from Workday: Navigate to **Academics -> Registration and Courses**, click the ⚙️ in the current class tab, and select **Download to Excel**.
2. Upload your class schedule in the provided format (an Excel file).
3. The application reads the file, extracts the necessary information (course names, times, locations), and generates events in a calendar.
4. The calendar events are saved as a `.ics` file.
5. You can then import the generated `.ics` file into your calendar application.



<p align="center">
  <img src="/images/ScreenShot1.jpeg" alt="Schedule2Calendar" width="500"/>
</p>  

### Example of Class Event

- **Course Name**: CPSC_V 213 - Introduction to Computer Systems
- **Location**: Room 101-6245 Agronomy Road Vancouver BC, Canada
- **Instructor**: Rubeus Hagrid
- **Time**: Monday, Wednesday, Friday from 14:00 PM to 15:30 PM

### Notifications
If you want to get **time to leave** notifications on iOS you can navigate to **Settings -> Apps -> Calendar -> Default Alert Time** and set the **Time to Leave** reminder so you don't miss your class. The application will notify you with enough time to navigate across campus and get to your classroom on time.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ubc-class-schedule-to-calendar.git
   ```

2. Install the dependencies:
    ```bash
    pip install Flask pandas icalendar
    ```

3. Run the Flask application:
    ```bash
    python3 Server.py
    ```

4. Open your browser and navigate to **http://127.0.0.1:5000/** to access the application.