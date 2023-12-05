#### Concatenate videos using ffmpeg 
```bash
ffmpeg -f concat -safe 0 -i ffmpeg_clips.txt -c copy output.mp4
```

#### Get duration of any MP4 file : 
```bash
ffmpeg -i your_video.mp4 2>&1 | grep Duration
```

```
ffmpeg -i saksham-cnu-test-1.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 output.wav
```

### Get audio file from video :
```bash
ffmpeg -i Lily.mp4 -acodec pcm_s16le -ar 44100 -ac 2 Lily.wav
```

### Get video with subtitle from audio: 
```bash
ffmpeg -f lavfi -i color=size=720x120:rate=25:color=black -i Lily.wav -vf "subtitles=Lily.srt:force_style='Fontsize=70'" -shortest audio_subbed.mp4
```4
## Get video with subtitles from video
```bash
ffmpeg -i Lily.mp4 -vf "subtitles=Lily.srt" -c:a copy Lily_Subbed.mp4
```