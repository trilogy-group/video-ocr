import os
import subprocess
import time

def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(
            f"Function {func.__name__} took {execution_time:.3f} seconds to execute"
        )
        return result

    return wrapper

@timeit
def concatenate_videos(output_filename, input_folder):
    # Create a text file containing the list of video clips
    input_textfile = 'ffmpeg_clips.txt'
    with open(input_textfile, 'w') as file:
        for filename in os.listdir(input_folder):
            if filename.endswith('.mp4'):
                file.write(f"file '{os.path.join(input_folder, filename)}'\n")

    # Run the ffmpeg command
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', input_textfile, '-c', 'copy', output_filename]
    subprocess.run(command)

    print('Concatenation completed!')

# Example usage:
output_filename = 'output.mp4'
input_folder = 'a62f733f-4cb6-4454-84f3-61a06a9b2713/webcam-capture-stream'
concatenate_videos(output_filename, input_folder)
