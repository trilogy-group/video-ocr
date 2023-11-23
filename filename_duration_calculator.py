import csv
from datetime import datetime, timedelta
import sys

# Function to convert duration in HH:MM:SS.SSS format to seconds
def duration_to_seconds(duration):
    time_format = "%H:%M:%S.%f"
    delta = datetime.strptime(duration, time_format) - datetime.strptime("00:00:00.000", time_format)
    return delta.total_seconds()

# Function to extract timestamp from the file name
def extract_timestamp(filename):
    timestamp_str = "-".join(filename.split('-')[3:7])
    return datetime.strptime(timestamp_str, "%H-%M-%S-%f").time()

# Check if the CSV file name is provided as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python script_name.py <csv_file>")
    sys.exit(1)

# CSV file containing video information
csv_file = sys.argv[1]

# Initialize variables for total duration and file with highest timestamp
total_duration = 0
file_with_highest_timestamp = None

# Read the CSV file and calculate total duration
with open(csv_file, 'r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header row
    for row in csv_reader:
        filename = row[0].strip()  # Assuming filename is in the first column
        duration = row[1].strip()  # Assuming duration is in the second column

        # Calculate duration in seconds
        duration_seconds = duration_to_seconds(duration)

        # Extract timestamp from the filename
        timestamp = extract_timestamp(filename)

        # Update total duration
        total_duration += duration_seconds

        # Check if the current file has the highest timestamp
        if file_with_highest_timestamp is None or timestamp > extract_timestamp(file_with_highest_timestamp[0]):
            file_with_highest_timestamp = (filename, duration)

# Calculate the duration of the file with the highest timestamp and add to total duration
if file_with_highest_timestamp:
    highest_timestamp_duration = duration_to_seconds(file_with_highest_timestamp[1])
    total_duration += highest_timestamp_duration

# Convert total duration back to HH:MM:SS.SSS format
total_duration_hms = str(timedelta(seconds=total_duration))

# Print the total duration
print(f"Total Duration: {total_duration_hms}")
