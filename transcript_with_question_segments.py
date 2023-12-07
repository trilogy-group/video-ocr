import json


def get_seconds(t):
    hours, minutes, seconds = map(int, t.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def get_transcript(st, et, words):
    st = get_seconds(st)
    et = get_seconds(et)
    transcript = ""
    for w in words:
        if not transcript and int(w["start"]) >= st:
            transcript = transcript + " " + w["punctuated_word"]
        elif transcript and int(w["end"]) <= et:
            transcript = transcript + " " + w["punctuated_word"]
        elif transcript and not transcript.endswith(".") and int(w["end"]) <= (et + 5):
            transcript = transcript + " " + w["punctuated_word"]
    return transcript


transcript = json.load(open("Lily_transcript.json", "r"))
question_segments = json.load(open("question_segments.json", "r"))

words = transcript["results"]["channels"][0]["alternatives"][0]["words"]

for question_id, segments in question_segments.items():
    if question_id == "No valid question detected":
        continue
    for segment in segments:
        segment["transcript"] = get_transcript(
            segment["start_time"], segment["end_time"], words
        )


json.dump(question_segments, open("qs_with_transcripts.json", "w"))
