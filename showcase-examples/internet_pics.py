import os
import requests
from bs4 import BeautifulSoup

def scrape_images(url, output_folder="images"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching the URL: {e}")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    image_tags = soup.find_all("img")
    if not image_tags:
        print("No images found on the page.")
        return

    for i, img in enumerate(image_tags):
        img_url = img.get("src")
        if not img_url:
            continue
        img_url = requests.compat.urljoin(url, img_url)
        
        try:
            img_response = requests.get(img_url, headers=headers)
            img_response.raise_for_status()
        except Exception as e:
            print(f"Could not download image {img_url}: {e}")
            continue
        ext = os.path.splitext(img_url)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        image_path = os.path.join(output_folder, f"image_{i}{ext}")

        with open(image_path, "wb") as f:
            f.write(img_response.content)
        print(f"Saved {img_url} as {image_path}")

if __name__ == "__main__":
    website_url = input("Enter the website URL: ").strip()
    scrape_images(website_url)
