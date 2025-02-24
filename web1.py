import os
import re
import zipfile
import requests
import fitz               # PyMuPDF
from flask import Flask, request, render_template_string, redirect, url_for
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import mammoth
import tempfile
import json

app = Flask(__name__)

################################################################################
#  GLOBAL LOG STORAGE
################################################################################
ALL_LOGS = []

def add_log(entry_type, message):
    """
    Add a log entry with a type/category and message.
    """
    ALL_LOGS.append({"type": entry_type, "message": message})

################################################################################
#  HTML TEMPLATE
################################################################################
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>All-in-One Utility</title>
    <style>
        body {
          font-family: Arial, sans-serif;
          background: #141414;
          color: #fff;
          margin: 0; 
          padding: 0;
        }
        header {
          background: linear-gradient(45deg, #6a0dad, #b53471);
          color: #fff;
          padding: 10px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        h1 {
          margin: 0;
        }
        nav a {
          margin-left: 20px;
          font-weight: bold;
          color: #fff;
          text-decoration: none;
        }
        nav a:hover {
          color: #e6e6e6;
        }
        .container {
          max-width: 960px;
          margin: 20px auto;
          padding: 20px;
        }
        .tabs {
          display: flex;
          border-bottom: 1px solid #333;
          margin-bottom: 15px;
        }
        .tabs button {
          background: none;
          border: none;
          color: #fff;
          padding: 10px 20px;
          cursor: pointer;
          font-size: 1em;
          transition: background 0.3s;
          outline: none;
        }
        .tabs button:hover,
        .tabs button.active {
          background: #333;
        }
        .tab-content {
          display: none;
        }
        .tab-content.active {
          display: block;
        }
        .upload-area {
          border: 2px dashed #9b59b6;
          border-radius: 10px;
          padding: 40px;
          text-align: center;
          background: #1f1f1f;
          transition: background-color 0.3s ease;
          cursor: pointer;
          margin-bottom: 15px;
        }
        .upload-area p {
          font-size: 1.2em;
          color: #a39fa7;
        }
        .upload-area input {
          display: none;
        }
        .file-icon {
          font-size: 3em;
          display: block;
          margin: 10px auto;
          color: #bb99ff;
        }
        label {
          display: block;
          margin-top: 1em;
          font-weight: bold;
        }
        input[type="text"], input[type="url"] {
          width: 100%;
          padding: 8px;
          margin-top: 5px;
          border: 1px solid #444;
          border-radius: 5px;
          background: #1f1f1f;
          color: #fff;
        }
        .btn {
          padding: 10px 20px;
          background: #9b59b6;
          border: none;
          color: #fff;
          cursor: pointer;
          border-radius: 5px;
          margin-top: 10px;
          transition: background 0.3s, transform 0.3s;
        }
        .btn:hover {
          background: #8655a3;
          transform: scale(1.05);
        }
        .logs {
          background: #1f1f1f;
          padding: 10px;
          border-radius: 10px;
          margin-top: 20px;
          max-height: 300px;
          overflow-y: auto;
        }
        .log-entry {
          border-bottom: 1px solid #333;
          padding: 5px 0;
        }
        .log-entry:last-child {
          border: none;
        }
        .log-type {
          font-weight: bold;
          margin-right: 5px;
          color: #ffcc00;
        }
        .log-message {
          color: #fff;
        }
        .success {
          color: #4cd137;
        }
        .error {
          color: #e84118;
        }
        .status-message {
          margin-top: 10px;
          font-weight: bold;
        }
    </style>
</head>
<body>
<header>
  <h1>All-in-One Utility</h1>
  <nav>
    <a href="#" onclick="switchTab('tab-home')">Home</a>
    <a href="#" onclick="switchTab('tab-logs')">Logs</a>
  </nav>
</header>
<div class="container">
  <div class="tabs">
    <button class="active" onclick="switchTab('tab-file-extract')">File Image Extract</button>
    <button onclick="switchTab('tab-youtube')">YouTube Transcript</button>
    <button onclick="switchTab('tab-article')">Article Scraper</button>
    <button onclick="switchTab('tab-webpics')">Website Image Scraper</button>
  </div>

  <!-- FILE IMAGE EXTRACT TAB -->
  <div id="tab-file-extract" class="tab-content active">
    <h2>Extract Images from .pdf, .pptx, or .docx</h2>
    <form action="{{ url_for('extract_images') }}" method="POST" enctype="multipart/form-data">
      <div class="upload-area" onclick="document.getElementById('file_input').click()">
        <p>Drag & Drop or Click to choose a PDF, PPTX, or DOCX file</p>
        <span class="file-icon">&#128196;</span>
        <input type="file" id="file_input" name="file" accept=".pdf, .pptx, .docx"/>
      </div>
      <button type="submit" class="btn">Extract Images</button>
    </form>
    {% if file_extract_status %}
      <p class="status-message">{{ file_extract_status }}</p>
    {% endif %}
  </div>

  <!-- YOUTUBE TRANSCRIPT TAB -->
  <div id="tab-youtube" class="tab-content">
    <h2>Fetch YouTube Transcript</h2>
    <form action="{{ url_for('youtube_transcript') }}" method="POST">
      <label for="youtube_url">YouTube URL:</label>
      <input type="url" id="youtube_url" name="youtube_url" required>
      <button type="submit" class="btn">Get Transcript</button>
    </form>
    {% if youtube_status %}
      <p class="status-message">{{ youtube_status }}</p>
    {% endif %}
    {% if youtube_transcript %}
      <div style="margin-top:15px; white-space:pre-wrap;">
        {{ youtube_transcript }}
      </div>
    {% endif %}
  </div>

  <!-- ARTICLE SCRAPER TAB -->
  <div id="tab-article" class="tab-content">
    <h2>Scrape Article Text</h2>
    <form action="{{ url_for('article_scraper') }}" method="POST">
      <label for="article_url">Article URL:</label>
      <input type="url" id="article_url" name="article_url" required>
      <button type="submit" class="btn">Scrape Article</button>
    </form>
    {% if article_status %}
      <p class="status-message">{{ article_status }}</p>
    {% endif %}
    {% if article_text %}
      <div style="margin-top:15px; white-space:pre-wrap;">
        {{ article_text }}
      </div>
    {% endif %}
  </div>

  <!-- WEBSITE IMAGE SCRAPER TAB -->
  <div id="tab-webpics" class="tab-content">
    <h2>Scrape Images from Website</h2>
    <form action="{{ url_for('internet_images') }}" method="POST">
      <label for="website_url">Website URL:</label>
      <input type="url" id="website_url" name="website_url" required>
      <button type="submit" class="btn">Scrape Images</button>
    </form>
    {% if webpics_status %}
      <p class="status-message">{{ webpics_status }}</p>
    {% endif %}
  </div>

  <!-- LOGS TAB -->
  <div id="tab-logs" class="tab-content">
    <h2>All Logs</h2>
    <div class="logs">
      {% for log in logs %}
        <div class="log-entry">
          <span class="log-type">[{{ log.type|upper }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      {% endfor %}
    </div>
  </div>
</div>

<script>
  function switchTab(tabId){
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(t => t.classList.remove('active'));

    const buttons = document.querySelectorAll('.tabs button');
    buttons.forEach(b => b.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    const btn = Array.from(buttons).find(b => b.textContent.trim() === document.getElementById(tabId).querySelector('h2').textContent.trim());
    if(btn){
      btn.classList.add('active');
    }
  }
</script>
</body>
</html>
"""

################################################################################
#  FUNCTIONS
#  1) Extract images from PPTX / DOCX / PDF
#  2) YouTube transcript
#  3) Article scraping
#  4) Internet images scraping
################################################################################

def extract_images_from_zip(in_memory_file, media_folder, output_folder):
    """
    Extract images from a zipped office file (pptx/docx).
    """
    with zipfile.ZipFile(in_memory_file, "r") as z:
        media_files = [f for f in z.namelist() if f.startswith(media_folder) and not f.endswith('/')]
        extracted_count = 0
        for file in media_files:
            data = z.read(file)
            filename = os.path.basename(file)
            out_path = os.path.join(output_folder, filename)
            with open(out_path, "wb") as f_out:
                f_out.write(data)
            extracted_count += 1
        return extracted_count

def extract_images_from_pdf(in_memory_file, output_folder):
    """
    Extract images from PDF using PyMuPDF.
    """
    extracted_count = 0
    try:
        with fitz.open(stream=in_memory_file.read(), filetype="pdf") as doc:
            for page_index in range(len(doc)):
                page = doc[page_index]
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue
                    image_bytes = base_image.get("image")
                    image_ext = base_image.get("ext", "png")
                    image_filename = f"page{page_index+1}_{img_index}.{image_ext}"
                    out_path = os.path.join(output_folder, image_filename)
                    with open(out_path, "wb") as f_out:
                        f_out.write(image_bytes)
                    extracted_count += 1
        return extracted_count
    except Exception as e:
        return 0

def get_youtube_transcript(video_url):
    """
    Return transcript text from YouTube URL using youtube_transcript_api.
    """
    def extract_video_id(url):
        pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL; cannot extract video ID.")
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = "\n".join(seg.get('text', '') for seg in transcript_list)
    return transcript_text

def scrape_article(url):
    """
    Scrape article text from a URL, preferring <article> tag, else <p> tags.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/115.0.0.0 Safari/537.36'
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    article_tag = soup.find('article')
    if article_tag:
        return article_tag.get_text(separator='\n', strip=True)
    else:
        paragraphs = soup.find_all('p')
        return "\n".join(p.get_text(strip=True) for p in paragraphs)

def scrape_images(url, output_folder="images"):
    """
    Scrape images from a given URL.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    image_tags = soup.find_all("img")
    downloaded_count = 0
    for i, img in enumerate(image_tags):
        img_url = img.get("src")
        if not img_url:
            continue
        img_url = requests.compat.urljoin(url, img_url)
        try:
            img_response = requests.get(img_url, headers=headers)
            img_response.raise_for_status()
        except Exception:
            continue
        ext = os.path.splitext(img_url)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        image_path = os.path.join(output_folder, f"image_{i}{ext}")
        with open(image_path, "wb") as f:
            f.write(img_response.content)
        downloaded_count += 1
    return downloaded_count

@app.route("/", methods=["GET"])
def index():
    """
    Render the main HTML page, along with any dynamic content we might have.
    """
    return render_template_string(
        HTML_TEMPLATE,
        logs=ALL_LOGS,
        file_extract_status=None,
        youtube_status=None,
        youtube_transcript=None,
        article_status=None,
        article_text=None,
        webpics_status=None,
    )

@app.route("/extract_images", methods=["POST"])
def extract_images():
    """
    Handle uploading a file (.pdf, .pptx, .docx) and extracting its images.
    """
    if 'file' not in request.files:
        add_log("error", "No file part in request.")
        return redirect(url_for("index"))

    file = request.files['file']
    if file.filename == '':
        add_log("error", "No selected file.")
        return redirect(url_for("index"))

    filename = file.filename.lower()
    _, ext = os.path.splitext(filename)
    ext = ext.lstrip('.')

    # Temporary folder to store images
    output_folder = "extracted_images"
    os.makedirs(output_folder, exist_ok=True)

    extracted_count = 0
    try:
        in_mem = file.read()
        if ext == 'pptx':
            with tempfile.TemporaryFile() as tf:
                tf.write(in_mem)
                tf.seek(0)
                extracted_count = extract_images_from_zip(tf, "ppt/media/", output_folder)
            add_log("info", f"Extracted {extracted_count} images from PPTX.")
        elif ext == 'docx':
            with tempfile.TemporaryFile() as tf:
                tf.write(in_mem)
                tf.seek(0)
                extracted_count = extract_images_from_zip(tf, "word/media/", output_folder)
            add_log("info", f"Extracted {extracted_count} images from DOCX.")
        elif ext == 'pdf':
            import io
            extracted_count = extract_images_from_pdf(io.BytesIO(in_mem), output_folder)
            add_log("info", f"Extracted {extracted_count} images from PDF.")
        else:
            add_log("error", f"Unsupported file extension: {ext}")
            return render_template_string(
                HTML_TEMPLATE,
                logs=ALL_LOGS,
                file_extract_status="Unsupported file extension.",
                youtube_status=None,
                youtube_transcript=None,
                article_status=None,
                article_text=None,
                webpics_status=None,
            )

        if extracted_count > 0:
            file_extract_status = f"Extraction complete. Saved {extracted_count} images in '{output_folder}'."
        else:
            file_extract_status = "No images found or error while extracting."
            add_log("error", f"No images found in file: {filename}.")

        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=file_extract_status,
            youtube_status=None,
            youtube_transcript=None,
            article_status=None,
            article_text=None,
            webpics_status=None,
        )
    except Exception as e:
        msg = f"Error extracting images: {e}"
        add_log("error", msg)
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=msg,
            youtube_status=None,
            youtube_transcript=None,
            article_status=None,
            article_text=None,
            webpics_status=None,
        )

@app.route("/youtube_transcript", methods=["POST"])
def youtube_transcript():
    """
    Fetch the YouTube transcript for a given URL.
    """
    url = request.form.get("youtube_url", "")
    if not url:
        add_log("error", "No YouTube URL provided.")
        return redirect(url_for("index"))
    try:
        transcript_text = get_youtube_transcript(url)
        add_log("info", f"Fetched transcript from YouTube URL: {url}")
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status="Transcript fetched successfully.",
            youtube_transcript=transcript_text,
            article_status=None,
            article_text=None,
            webpics_status=None,
        )
    except Exception as e:
        msg = f"Error fetching transcript: {e}"
        add_log("error", msg)
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status=msg,
            youtube_transcript=None,
            article_status=None,
            article_text=None,
            webpics_status=None,
        )

@app.route("/article_scraper", methods=["POST"])
def article_scraper():
    """
    Scrape an article from a given URL.
    """
    url = request.form.get("article_url", "")
    if not url:
        add_log("error", "No article URL provided.")
        return redirect(url_for("index"))
    try:
        text = scrape_article(url)
        add_log("info", f"Scraped article from URL: {url}")
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status=None,
            youtube_transcript=None,
            article_status="Successfully scraped article.",
            article_text=text,
            webpics_status=None,
        )
    except Exception as e:
        msg = f"Error scraping article: {e}"
        add_log("error", msg)
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status=None,
            youtube_transcript=None,
            article_status=msg,
            article_text=None,
            webpics_status=None,
        )

@app.route("/internet_images", methods=["POST"])
def internet_images():
    """
    Scrape images from the given website URL.
    """
    url = request.form.get("website_url", "")
    if not url:
        add_log("error", "No website URL provided.")
        return redirect(url_for("index"))
    output_folder = "scraped_images"
    os.makedirs(output_folder, exist_ok=True)
    try:
        downloaded_count = scrape_images(url, output_folder=output_folder)
        msg = f"Scraped {downloaded_count} images from {url} into '{output_folder}'."
        add_log("info", msg)
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status=None,
            youtube_transcript=None,
            article_status=None,
            article_text=None,
            webpics_status=msg,
        )
    except Exception as e:
        msg = f"Error scraping images: {e}"
        add_log("error", msg)
        return render_template_string(
            HTML_TEMPLATE,
            logs=ALL_LOGS,
            file_extract_status=None,
            youtube_status=None,
            youtube_transcript=None,
            article_status=None,
            article_text=None,
            webpics_status=msg,
        )

################################################################################
if __name__ == "__main__":
    # Make sure folders exist for storing extracted images
    os.makedirs("extracted_images", exist_ok=True)
    os.makedirs("scraped_images", exist_ok=True)
    app.run(debug=True)
