import csv
from datetime import datetime, timedelta
import sys

# Function to convert duration in HH:MM:SS.SSS format to seconds
def duration_to_seconds(duration):
    time_format = "%H:%M:%S.%f"
    delta = datetime.strptime(duration, time_format) - datetime.strptime("00:00:00.000", time_format)
    return delta.total_seconds()

# Check if the CSV file name is provided as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python script_name.py <csv_file>")
    sys.exit(1)

# CSV file containing video information
csv_file = sys.argv[1]

# Initialize total duration
total_duration = 0

# Read the CSV file and calculate total duration
with open(csv_file, 'r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header row
    for row in csv_reader:
        duration = row[1].strip()  # Assuming duration is in the second column
        total_duration += duration_to_seconds(duration)

# Convert total duration back to HH:MM:SS.SSS format
total_duration_hms = str(timedelta(seconds=total_duration))

# Print the total duration
print(f"Total Duration: {total_duration_hms}")
