from flask import Flask, request, send_file, render_template, url_for
import pandas as pd
from icalendar import Calendar, Event, vRecur
from datetime import datetime, timedelta
import os
import re
import csv
import json


app = Flask(__name__)


# Load address map from CSV
def load_addresses(csv_path):
    address_map = {}
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # skip header if present
        for row in reader:
            building_name, code, address = row
            code = code.strip().upper()
            address_map[code] = {
                "name": building_name.strip(),
                "address": address.strip(),
            }
    return address_map


ADDRESS_MAP = load_addresses("Address.csv")


# Function to parse location and append full address
def parse_address(location, address_map):
    if not location or not str(location).strip():
        return "Unknown Address"
    loc = str(location).strip()

    if loc.lower().startswith("online"):
        return "Online - Virtual Class\nCanada"

    # Try new format: "... (HENN) | ... | Room: 200"
    m_code = re.search(r"\(([A-Z0-9]+)\)", loc)
    m_room = re.search(r"Room:\s*([A-Za-z0-9\-]+)", loc)

    code = m_code.group(1).upper() if m_code else None
    room = m_room.group(1) if m_room else None

    # Fallback to old format: "HENN - Room 200"
    if not code:
        parts = loc.split("-")
        if parts:
            code = parts[0].strip().upper()
        if len(parts) >= 2 and not room:
            room = parts[-1].strip().replace("Room", "").strip()

    if code in address_map:
        addr = address_map[code]["address"]
        if room:
            return f"{room}-{addr}\nVancouver BC\nCanada"
        return f"{addr}\nVancouver BC \nCanada"

    return "Unknown Address"


# Function to get the full building name
def get_building_full_name(location, address_map):
    if not location or not str(location).strip():
        return str(location)

    loc = str(location).strip()
    if loc.lower().startswith("online"):
        return "💻 Online Class"

    # New format: "... | Hennings Building (HENN) | Floor: 1 | Room: 200"
    m_code = re.search(r"\(([A-Z0-9]+)\)", loc)
    code = m_code.group(1).upper() if m_code else None
    pieces = [p.strip() for p in loc.split("|")]
    human_name = None
    if len(pieces) >= 2:
        # remove trailing "(CODE)" from the building name
        human_name = re.sub(r"\s*\([A-Z0-9]+\)\s*$", "", pieces[1]).strip()

    m_room = re.search(r"Room:\s*([A-Za-z0-9\-]+)", loc)
    room = m_room.group(1) if m_room else None

    if code in address_map:
        name = human_name or address_map[code]["name"]
        if room:
            return f"📍{name} ({code}) - Room {room}"
        return f"📍{name} ({code})"

    # Fallbacks
    if code and room:
        return f"📍{code} - Room {room}"
    return loc


# Function to parse time
def parse_time(time_str):
    time_str = time_str.lower().replace(".", "").replace("|", "").strip()
    return datetime.strptime(time_str, "%I:%M %p").time()


# Function to parse meeting patterns
def parse_meeting_pattern(pattern):
    parts = pattern.strip().split(" | ")

    if len(parts) < 3:
        raise ValueError(f"Invalid pattern format: {pattern}")

    # Always present
    dates = parts[0].strip()
    days = parts[1].strip()
    times = parts[2].strip()

    # Flexible location handling
    if len(parts) >= 4:
        location_parts = parts[3:]
        location = " | ".join(location_parts).strip()
    else:
        location = "Online"

    # Time parsing
    start_time, end_time = map(parse_time, times.split(" - "))
    start_date, end_date = map(
        lambda x: datetime.strptime(x.strip(), "%Y-%m-%d").date(), dates.split(" - ")
    )

    return start_date, end_date, days.split(), start_time, end_time, location


# Function to create an event
def create_event(
    name, start_datetime, end_datetime, location, address="", description=""
):
    event = Event()
    event.add("summary", name)
    event.add("dtstart", start_datetime)
    event.add("dtend", end_datetime)
    event.add("location", address)
    event.add("description", description)
    return event


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    # Save the uploaded file
    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
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
    days_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

    for _, row in df.iterrows():
        if (
            pd.isna(row.get("Meeting Patterns"))
            or not str(row["Meeting Patterns"]).strip()
        ):
            continue
        name = f"{row['Course Listing']} - {row['Instructional Format']}"  # Combine course name and format
        meeting_patterns = row["Meeting Patterns"]
        instructor = row.get("Instructor", "")
        details = row.get("Section", "")
        patterns = re.split(r"\n(?=\d{4})", meeting_patterns)

        for pattern in patterns:
            start_date, end_date, days, start_time, end_time, location = (
                parse_meeting_pattern(pattern)
            )
            weekday_map = {
                "Mon": "MO",
                "Tue": "TU",
                "Wed": "WE",
                "Thu": "TH",
                "Fri": "FR",
                "Sat": "SA",
                "Sun": "SU",
            }
            byday = [weekday_map[day] for day in days if day in weekday_map]

            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(start_date, end_time) - timedelta(
                minutes=10
            )
            full_address = parse_address(location, ADDRESS_MAP)
            building_full_description = get_building_full_name(location, ADDRESS_MAP)
            description = (
                f"Instructor: {instructor}\n\n{building_full_description}\n\n{details}"
            )

            event = create_event(
                name, start_datetime, end_datetime, location, full_address, description
            )
            event.add(
                "rrule",
                vRecur(
                    {
                        "freq": "weekly",
                        "byday": byday,
                        "until": datetime.combine(end_date, end_time)
                        - timedelta(minutes=10),
                    }
                ),
            )
            cal.add_component(event)

    ics_file_path = os.path.join("uploads", f"{os.path.splitext(file.filename)[0]}.ics")
    with open(ics_file_path, "wb") as f:
        f.write(cal.to_ical())

    return send_file(ics_file_path, as_attachment=True)


def load_howto_items():
    img_dir = os.path.join(app.static_folder, "howto")
    try:
        files = sorted(
            f
            for f in os.listdir(img_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        )
    except FileNotFoundError:
        files = []

    # optional metadata file: static/howto/meta.json
    meta_path = os.path.join(img_dir, "meta.json")
    meta = {}
    try:
        with open(meta_path, "r") as fh:
            data = json.load(fh)
            # allow either list of objects or object keyed by filename
            if isinstance(data, list):
                meta = {item["file"]: item for item in data if "file" in item}
            elif isinstance(data, dict):
                meta = data
    except Exception:
        meta = {}

    items = []
    for f in files:
        base = os.path.splitext(f)[0]
        default_caption = base.replace("_", " ").strip()
        m = meta.get(f, {})
        items.append(
            {
                "file": f,
                "caption": m.get("caption", default_caption),
                "alt": m.get("alt", default_caption),
            }
        )
    return items


@app.get("/how-to")
def how_to():
    items = load_howto_items()
    return render_template("how_to.html", items=items)


if __name__ == "__main__":
    app.run(debug=True)
