from flask import Flask, request, send_file, render_template
import pandas as pd
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import os
import re
import csv

app = Flask(__name__)

# Load address map from CSV
def load_addresses(csv_path):
    address_map = {}
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row if you have one
        for row in reader:
            building_name, code, address = row
            # Store both name and address in a dictionary for each code
            address_map[code] = {
                "name": building_name,
                "address": address
            }
    return address_map


ADDRESS_MAP = load_addresses('Address.csv')

# Function to parse location and append full address
def parse_address(location, address_map):
    parts = location.split('-')
    if len(parts) >= 2:
        building_code = parts[0].strip()
        room_info = parts[-1].strip()
        
        # Remove "Room" if it appears at the beginning
        if room_info.startswith("Room"):
            room_info = room_info[5:].strip()
        
        if building_code in address_map:
            building_address = address_map[building_code]["address"]
            # Format full address as requested
            return f"{room_info}-{building_address}\nVancouver BC V6T 1Z4\nCanada"
    return "Unknown Address"

# Function to get the full building name
def get_building_full_name(location, address_map):
    parts = location.split('-')
    if len(parts) >= 2:
        building_code = parts[0].strip()
        room_info = '-'.join(parts[1:]).strip() 
        
        if building_code in address_map:
            building_name = address_map[building_code]["name"]
            return f"📍{building_name} ({building_code})-{room_info}"
    return location

# Function to parse time
def parse_time(time_str):
    time_str = time_str.replace('.', '')  # Remove periods from time strings
    return datetime.strptime(time_str, '%I:%M %p').time()

# Function to parse meeting patterns
def parse_meeting_pattern(pattern):
    dates, days, times, location = pattern.split(' | ')
    start_date, end_date = map(lambda x: datetime.strptime(x, '%Y-%m-%d').date(), dates.split(' - '))
    start_time, end_time = map(parse_time, times.split(' - '))
    return start_date, end_date, days.split(), start_time, end_time, location

# Function to create an event
def create_event(name, start_datetime, end_datetime, location, address='', description=''):
    event = Event()
    event.add('summary', name)
    event.add('dtstart', start_datetime)
    event.add('dtend', end_datetime)
    event.add('location', address)
    event.add('description', description)
    return event

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    # Save the uploaded file
    file_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(file_path)
    
    # Process the file and generate the .ics
    df_initial = pd.read_excel(file_path, header=None)
    row_with_course_listing = None
    for i, row in df_initial.iterrows():
        if "Course Listing" in row.values:
            row_with_course_listing = i
            break

    if row_with_course_listing is not None:
        df = pd.read_excel(file_path, skiprows=row_with_course_listing)
    else:
        return "Could not find 'Course Listing' in the Excel file.", 400

    cal = Calendar()
    days_map = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}

    for _, row in df.iterrows():
        name = f"{row['Course Listing']} - {row['Instructional Format']}"  # Combine course name and format
        meeting_patterns = row['Meeting Patterns']
        instructor = row.get('Instructor', '')
        details = row.get('Section', '')
        patterns = re.split(r'\n(?=\d{4})', meeting_patterns)

        for pattern in patterns:
            start_date, end_date, days, start_time, end_time, location = parse_meeting_pattern(pattern)
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.strftime('%a')[:3] in days_map and days_map[current_date.strftime('%a')[:3]] in [days_map[day] for day in days]:
                    start_datetime = datetime.combine(current_date, start_time)
                    end_datetime = datetime.combine(current_date, end_time)
                    full_address = parse_address(location, ADDRESS_MAP)
                    building_full_description = get_building_full_name(location, ADDRESS_MAP)
                    description = f'Instructor: {instructor}\n\n{building_full_description}\n\n{details}'
                    event = create_event(name, start_datetime, end_datetime, location, full_address, description)
                    cal.add_component(event)
                
                current_date += timedelta(days=1)
    
    ics_file_path = os.path.join('uploads', f'{os.path.splitext(file.filename)[0]}.ics')
    with open(ics_file_path, 'wb') as f:
        f.write(cal.to_ical())

    return send_file(ics_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
