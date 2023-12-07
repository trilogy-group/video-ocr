"""
This module offers functionality to OCR the frames of a video, while trying to be
computationally efficient by ignoring frames that are similar to their adjacent
frames.
"""
import cv2 as cv
import os

import scipy.fft
from contextlib import contextmanager
from itertools import tee
import numpy as np
import tesserocr
from PIL import Image
from multiprocessing.pool import ThreadPool
import multiprocessing
import tqdm
import click
from functools import wraps
import time
from collections import deque
import re
import boto3
import threading
from collections import defaultdict
import json

IS_CL = True
FILEPATH_DOC = "Path to the input video file"
SAMPLE_RATE_DOC = "Number of frames to sample per second"
DEBUG_DIR_DOC = (
    "If provided, writes frame and their respective texts here, for debugging"
)
NO_VALID_QUESTION_OCR_DIR_DOC = (
    "If provided, writes frame and their respective texts here, for frames where no questions detected"
)


def _only_if_cl(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if IS_CL:
            return f(*args, **kwargs)

    return wrapper


@_only_if_cl
def _error_log(text, *args, **kwargs):
    click.echo(click.style(text, fg="red"), err=True, *args, **kwargs)


@_only_if_cl
def _info_log(text, *args, **kwargs):
    click.echo(text, *args, **kwargs)

class ThreadLocalTextractClient:
    def __init__(self):
        self.local = threading.local()

    def get(self):
        if not hasattr(self.local, "client"):
            self.local.client = boto3.client(
                "textract",
                region_name="us-east-1",
            )
        return self.local.client


_textract_client_singleton = ThreadLocalTextractClient()


class _NoOpProgressBar:
    def update(self):
        pass

    def total(self, n):
        pass


pbar = _NoOpProgressBar()


def phash(image, hash_size=8, highfreq_factor=4):
    img_size = hash_size * highfreq_factor
    image = cv.resize(image, (img_size, img_size), interpolation=cv.INTER_LINEAR)
    dct = scipy.fft.dct(scipy.fft.dct(image, axis=0), axis=1)
    dctlowfreq = dct[:hash_size, :hash_size]
    med = np.median(dctlowfreq)
    diff = dctlowfreq > med
    return diff


class Frame:
    def __init__(self, frame_number, image, ts_second):
        self.frame_number = frame_number
        self.image = image
        self.ts_second = ts_second


@contextmanager
def _open_cv_video(filepath):
    cap = cv.VideoCapture(filepath)
    try:
        yield cap
    finally:
        cap.release()

def _get_cropped_frame(frame, top_percentage=0.25):
    # Get the dimensions of the frame
    height, width = frame.shape[:2]

    # Calculate the height of the top portion to keep
    top_height = int(height * top_percentage)

    # Select the region of interest (ROI) corresponding to the top portion
    cropped_frame = frame[:top_height, :]

    return cropped_frame


def _get_frames(video_capture, sample_rate):
    fps = int(video_capture.get(cv.CAP_PROP_FPS))
    _info_log(f"{fps=}")
    pbar.total = (
        video_capture.get(cv.CAP_PROP_FRAME_COUNT) // (fps // sample_rate)
    ) - 1
    frame_number = 0
    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break
        frame_number += 1
        if frame_number % (fps // sample_rate) != 0:
            continue
        frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # cropped_frame = _get_cropped_frame(frame)
        yield Frame(frame_number, frame, frame_number // fps)


def _pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def _are_similar_frame(f1, f2):
    diff = np.count_nonzero(phash(f1.image) != phash(f2.image))
    return diff == 0


def _filter_redundant_frames(frames):

    # Create a deque to store frames
    frame_buffer = deque(maxlen=2)

    # for f1, f2 in _pairwise(frames):
    #     if not _are_similar_frame(f1, f2):
    #         yield f1
    #     else:
    #         pbar.update()

    for frame in frames:
        # Add the current frame to the deque
        frame_buffer.append(frame)

        if len(frame_buffer) < 2:
            yield frame
        else:
            f1, f2 = frame_buffer
            if not _are_similar_frame(f1, f2):
                yield f2
            else:
                pbar.update()


# def _ocr(frame):
#     frame.image = _get_cropped_frame(frame.image)
#     pil_image = Image.fromarray(frame.image)
#     text = tesserocr.image_to_text(pil_image)
#     frame.text = text
#     pbar.update()
#     return frame

def _ocr(frame):
    frame.image = _get_cropped_frame(frame.image)
    client = _textract_client_singleton.get()
    response = client.detect_document_text(
                    Document={"Bytes": cv.imencode(".jpg", frame.image)[1].tobytes()}
                )
    text = "\n".join(
        [
            item["Text"]
            for item in response["Blocks"]
            if "Text" in item and item["BlockType"] == "LINE"
        ]
    )
    frame.text = text
    pbar.update()
    return frame


def _parallel_ocr(frames):
    with ThreadPool(multiprocessing.cpu_count()) as pool:
        return pool.map(_ocr, frames, chunksize=multiprocessing.cpu_count())


def _write_if_debug(frames, debug_dir):
    if not debug_dir:
        return
    for frame in frames:
        cv.imwrite(os.path.join(debug_dir, f"{frame.frame_number}.png"), frame.image)
        with open(os.path.join(debug_dir, f"{frame.frame_number}.txt"), "w") as f:
            f.write(frame.text)


def perform_video_ocr(filepath: str, sample_rate: int = 1, debug_dir: str = ""):
    f"""
    :param filepath: {FILEPATH_DOC}
    :param sample_rate: {SAMPLE_RATE_DOC}
    :param debug_dir: {DEBUG_DIR_DOC}
    """
    frames = []
    with _open_cv_video(filepath) as cap:
        frames = _parallel_ocr(_filter_redundant_frames(_get_frames(cap, sample_rate)))
    frames.sort(key=lambda frame: frame.frame_number)
    non_empty_frames = []
    for frame in frames:
        if frame.text.strip():
            non_empty_frames.append(frame)
    _write_if_debug(non_empty_frames, debug_dir)
    return non_empty_frames


def _get_formatted_time(seconds):
    rem_seconds = seconds
    hours = rem_seconds // 3600
    rem_seconds %= 3600
    mins = rem_seconds // 60
    rem_seconds %= 60
    return "{:02}:{:02}:{:02}".format(int(hours), int(mins), int(rem_seconds))


def _display_frames(frames):
    terminal_width = os.get_terminal_size().columns
    _info_log("")
    for frame in frames:
        _info_log("-" * terminal_width)
        _info_log(f"Timestamp = {_get_formatted_time(frame.ts_second)}")
        _info_log(frame.text)
    _info_log("-" * terminal_width)

def _get_question_number(ocr_text):

    # Define the regex pattern for matching the question number
    regex_pattern = r"Question\s+(\d+)\s*[\/|lI1]\s*(\d+)"

    # Search for the regex pattern in the text
    match = re.search(regex_pattern, ocr_text)

    # Check if a match is found
    if match:
        return match.group(1)
    else:
        return "No valid question detected"


def _display_question_segments(frames, no_valid_question_ocr_dir):

    no_valid_question_ocr_frames = []
    for frame in frames:
        question_number = _get_question_number(frame.text)
        _info_log(f"{_get_formatted_time(frame.ts_second)} ({frame.frame_number}) -> {question_number}")
        if question_number == "No valid question detected":
            no_valid_question_ocr_frames.append(frame)
    
    _info_log(f"Number of frames with no valid question detected : {len(no_valid_question_ocr_frames)}")
    _write_if_debug(no_valid_question_ocr_frames, no_valid_question_ocr_dir)


def _prepare_question_segments(frames):

    question_time_frame_ranges = defaultdict(list)
    previous_question_number = None

    for frame in frames:
        current_question_number = _get_question_number(frame.text)
        current_time = _get_formatted_time(frame.ts_second)
        if current_question_number != previous_question_number:
            question_time_frame_ranges[current_question_number].append({"start_time": current_time, "end_time": current_time})
        else:
            question_time_frame_ranges[current_question_number][-1]["end_time"] = current_time
        previous_question_number = current_question_number
    
    json.dump(question_time_frame_ranges, open("question_segments.json", "w"))


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

@click.command()
@click.argument(
    "filepath",
    type=click.Path(
        exists=True,
        readable=True,
    ),
)
@click.option("--sample_rate", type=int, help=SAMPLE_RATE_DOC, default=1)
@click.option(
    "--debug_dir",
    type=click.Path(exists=True, writable=True, file_okay=False, dir_okay=True),
    help=DEBUG_DIR_DOC,
)
@click.option(
    "--no_valid_question_ocr_dir",
    type=click.Path(exists=True, writable=True, file_okay=False, dir_okay=True),
    help=NO_VALID_QUESTION_OCR_DIR_DOC,
)
@timeit
def main(filepath, sample_rate, debug_dir, no_valid_question_ocr_dir):
    global IS_CL
    global pbar
    IS_CL = True
    with tqdm.tqdm() as progress_bar:
        pbar = progress_bar
        frames = perform_video_ocr(
            filepath, sample_rate=sample_rate, debug_dir=debug_dir
        )
        
    _info_log(f"Total number of frames found : {len(frames)}")
    # _display_frames(frames)
    _display_question_segments(frames, no_valid_question_ocr_dir)
    # _prepare_question_segments(frames)


if IS_CL:
    main()
