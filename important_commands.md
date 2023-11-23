#### Concatenate videos using ffmpeg 
```bash
ffmpeg -f concat -safe 0 -i ffmpeg_clips.txt -c copy output.mp4
```

#### Get duration of any MP4 file : 
```bash
ffmpeg -i your_video.mp4 2>&1 | grep Duration
```