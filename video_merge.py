from moviepy.editor import VideoFileClip, concatenate_videoclips
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor

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

def read_and_trim_lines(file_path):
    try:
        with open(file_path, 'r') as file:
            # Read lines and remove '\n' from each line
            lines = [line.rstrip('\n') for line in file.readlines()]
            return lines
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

@timeit
def merge_video_clips(input_paths, output_path, batch_size=50):
    clip_batches = [input_paths[i:i + batch_size] for i in range(0, len(input_paths), batch_size)]

    final_clips = []
    for clip_batch in clip_batches:
        clips = [VideoFileClip(clip_path) for clip_path in clip_batch]
        merged_clip = concatenate_videoclips(clips, method="compose")
        final_clips.append(merged_clip)

    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(output_path)

@timeit
def merge_video_clips_recursive(input_paths, output_path, path_prefix, batch_size, iteration):
    # Base case: if there's only one clip, no need to merge further
    if len(input_paths) == 1:
        return VideoFileClip(input_paths[0]).write_videofile(output_path)

    # Divide the input clips into batches
    clip_batches = [input_paths[i:i + batch_size] for i in range(0, len(input_paths), batch_size)]

    # Recursively merge each batch with a batch size of 50 for the first iteration
    merged_clips = []
    for i, clip_batch in enumerate(clip_batches):
        # Check if there's only one clip in the batch
        if len(clip_batch) == 1:
            merged_clips.append(clip_batch[0])
        else:
            merged_clip_path = f"{path_prefix}merged-clips/merged_clip_i{iteration}_{i}.mp4"
            concatenate_videoclips([VideoFileClip(clip_path) for clip_path in clip_batch], method="compose").write_videofile(merged_clip_path)
            merged_clips.append(merged_clip_path)

    # Update batch size to 2 for the next iterations
    return merge_video_clips_recursive(merged_clips, output_path, path_prefix, batch_size=2, iteration=iteration+1)

def merge_batch(clip_batch, path_prefix, iteration, i):
    if len(clip_batch) == 1:
        return clip_batch[0]
    else:
        merged_clip_path = f"{path_prefix}merged-clips-parallel/merged_clip_{i}_i{iteration}.mp4"
        concatenate_videoclips([VideoFileClip(clip_path) for clip_path in clip_batch], method="compose").write_videofile(merged_clip_path)
        return merged_clip_path

@timeit
def merge_video_clips_parallel(input_paths, output_path, path_prefix, batch_size, iteration):
    
    # Base case: if there's only one clip, no need to merge further
    if len(input_paths) == 1:
        return VideoFileClip(input_paths[0]).write_videofile(output_path)

    # Divide the input clips into batches
    clip_batches = [input_paths[i:i + batch_size] for i in range(0, len(input_paths), batch_size)]

    # Run the loop in parallel
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(merge_batch, clip_batches, [path_prefix] * len(clip_batches), [iteration] * len(clip_batches), range(len(clip_batches))))

    # Collect the results
    merged_clips = [result for result in results if result]
    merged_clips = sorted(merged_clips)

    # Update batch size to 2 for the next iterations
    return merge_video_clips_parallel(merged_clips, output_path, path_prefix, batch_size=2, iteration=iteration+1)

path_prefix = "video-stream/webcam-capture-stream/"
input_clips = [f"{path_prefix}{filename}" for filename in read_and_trim_lines("video-stream/clips.txt")]
output_file = "video-stream/merged_video_parallel.mp4"

merge_video_clips_parallel(input_clips, output_file, path_prefix, 50, 0)
# merge_video_clips(input_clips, output_file, 50)
# merge_video_clips_recursive(input_clips, output_file, path_prefix, 50, 0)