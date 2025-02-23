from youtube_transcript_api import YouTubeTranscriptApi
import re

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
        for segment in transcript:
            print(segment['text'])
    else:
        print("No transcript available.")

if __name__ == '__main__':
    main()
