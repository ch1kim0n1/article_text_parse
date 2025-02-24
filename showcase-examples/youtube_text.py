from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

def get_transcript_from_url(url):
    video_id = extract_video_id(url)
    if not video_id:
        print("Error: Unable to extract video ID from the provided URL.")
        return None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print("Error fetching transcript:", e)
        return None

def main():
    video_url = input("Please paste the YouTube video URL: ")
    transcript = get_transcript_from_url(video_url)
    if transcript:
        full_text = ""
        for segment in transcript:
            segment_text = segment.get('text', '')
            print(segment_text)
            full_text += segment_text + "\n"
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "transcript.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Transcript saved to {file_path}")
    else:
        print("No transcript available.")

if __name__ == '__main__':
    main()
