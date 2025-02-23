from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# This HTML template mimics the design from your uploaded file.
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Vanilla HTML Web Scraper with Python Backend</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 40px;
    }
    input[type="text"] {
      width: 80%;
      padding: 10px;
      font-size: 16px;
    }
    button {
      padding: 10px 20px;
      font-size: 16px;
      margin-left: 10px;
      cursor: pointer;
    }
    #output {
      width: 100%;
      height: 300px;
      margin-top: 20px;
      padding: 10px;
      font-size: 14px;
      border: 1px solid #ccc;
      white-space: pre-wrap;
      overflow-y: auto;
      background: #f9f9f9;
    }
  </style>
</head>
<body>
  <h1>Vanilla HTML Web Scraper</h1>
  <form action="/scrape" method="post">
    <input type="text" name="url" placeholder="Enter webpage URL" required>
    <button type="submit">Scrape</button>
  </form>
  {% if scraped_text %}
  <h2>Scraped Text:</h2>
  <div id="output">{{ scraped_text }}</div>
  {% endif %}
</body>
</html>
'''

def scrape_article(url):
    # Use a browser-like user-agent header to help bypass basic bot protections.
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/115.0.0.0 Safari/537.36'
        )
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an error for bad status codes
    except Exception as e:
        return f"Error retrieving URL: {e}"
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # First try to extract content from an <article> tag
    article_tag = soup.find('article')
    if article_tag:
        article_text = article_tag.get_text(separator='\n', strip=True)
    else:
        # Fallback: Combine text from all <p> tags
        paragraphs = soup.find_all('p')
        article_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    
    return article_text

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form.get('url')
    scraped_text = scrape_article(url)
    
    # Print the scraped text to the terminal
    print("\n--- Scraped Article Text ---\n")
    print(scraped_text)
    
    # Save the scraped text to a file
    with open("scraped_article.txt", "w", encoding="utf-8") as f:
        f.write(scraped_text)
    
    return render_template_string(HTML_TEMPLATE, scraped_text=scraped_text)

if __name__ == "__main__":
    app.run(debug=True)
