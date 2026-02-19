import os
import requests
import hashlib
import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class MultiImageScraper:
    def __init__(self, download_path="./downloads"):
        self.download_path = download_path
        self.seen_hashes = set()  # Track unique images via MD5
        
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # Headless Chrome setup
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def get_image_urls(self, engine_url, target_count):
        self.driver.get(engine_url)
        urls = set()
        
        # Scroll to load more images (basic implementation)
        while len(urls) < target_count:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find image tags (selectors vary by engine; 'img' is the generic fallback)
            thumbnails = self.driver.find_elements(By.TAG_NAME, "img")
            for img in thumbnails:
                src = img.get_attribute("src")
                if src and "http" in src:
                    urls.add(src)
                if len(urls) >= target_count:
                    break
        return list(urls)

    def download_and_deduplicate(self, url):
        try:
            response = requests.get(url, timeout=10)
            image_content = response.content
            
            # Create a unique hash for the image data
            img_hash = hashlib.md5(image_content).hexdigest()
            
            if img_hash not in self.seen_hashes:
                self.seen_hashes.add(img_hash)
                
                # Save the image
                img = Image.open(BytesIO(image_content)).convert("RGB")
                file_path = os.path.join(self.download_path, f"{img_hash}.jpg")
                img.save(file_path, "JPEG")
                return True
        except Exception as e:
            return False
        return False

    def run(self, keyword, count_per_engine):
        engines = {
            "Google": f"https://www.google.com/search?q={keyword}&tbm=isch",
            "Bing": f"https://www.bing.com/images/search?q={keyword}",
            "DuckDuckGo": f"https://duckduckgo.com/?q={keyword}&iax=images&ia=images",
            "Yahoo": f"https://images.search.yahoo.com/search/images?p={keyword}"
        }

        for name, url in engines.items():
            print(f"--- Scraping {name} ---")
            found_urls = self.get_image_urls(url, count_per_engine)
            
            success_count = 0
            for img_url in found_urls:
                if self.download_and_deduplicate(img_url):
                    success_count += 1
            print(f"Downloaded {success_count} unique images from {name}.")

        self.driver.quit()

# Usage
if __name__ == "__main__":
    scraper = MultiImageScraper(download_path="./my_dataset")
    scraper.run(keyword="cyberpunk architecture", count_per_engine=10)