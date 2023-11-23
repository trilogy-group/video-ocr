#!/bin/bash

# Check if the output file is provided as a command-line argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <output_file>"
    exit 1
fi

# Output file to store results
output_file="$1"

# Remove the existing output file if it exists
rm -f "$output_file"

# Iterate over all MP4 files in the current directory
for file in *.mp4; do
    # Check if the file is a regular file (not a directory)
    if [ -f "$file" ]; then
        # Run FFmpeg command to get duration and bitrate
        ffmpeg_output=$(ffmpeg -i "$file" 2>&1 | grep 'Duration\|bitrate')

        # Extract duration and bitrate from FFmpeg output
        duration=$(echo "$ffmpeg_output" | grep -oP "Duration: \K[0-9:.]+")
        bitrate=$(echo "$ffmpeg_output" | grep -oP "bitrate: \K[0-9]+")

        # Print the information to the console
        echo "File: $file, Duration: $duration, Bitrate: $bitrate"

        # Append the information to the output file
        echo "$file, $duration, $bitrate" >> "$output_file"
    fi
done

echo "Video information has been saved to $output_file"
