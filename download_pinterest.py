import requests
import re
import os
from urllib.parse import urlparse

URL = "https://pin.it/2ZczqqkCW"
OUTPUT_DIR = "pinterest_raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print(f"Resolving Pinterest URL: {URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Resolve the short link redirection
    response = requests.get(URL, headers=headers, allow_redirects=True)
    final_url = response.url
    print(f"Final resolved URL: {final_url}")
    
    # Check if we got redirected to a Pinterest pin page
    html = response.text
    
    # Search for og:image or pin image URLs in the HTML
    # Typically: <meta property="og:image" content="https://i.pinimg.com/..."/>
    og_images = re.findall(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
    if not og_images:
        # Try alternate pattern
        og_images = re.findall(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
        
    if not og_images:
        # Look for any large images on pinimg.com
        og_images = re.findall(r'https://i.pinimg.com/[a-zA-Z0-9_/.-]+', html)

    if og_images:
        # Filter duplicates and pick the highest resolution one
        # Pin images on pinimg.com usually have sizes like /originals/ or /736x/ or /564x/ or /236x/
        # We prefer originals
        unique_urls = list(set(og_images))
        print("Found image URLs on page:")
        for u in unique_urls:
            print(f" - {u}")
            
        # Select best URL
        best_url = None
        for path_type in ["/originals/", "/736x/", "/564x/"]:
            for u in unique_urls:
                if path_type in u:
                    best_url = u
                    break
            if best_url:
                break
                
        if not best_url:
            best_url = unique_urls[0]
            
        # Download the image
        print(f"Downloading best image URL: {best_url}")
        img_resp = requests.get(best_url, headers=headers)
        if img_resp.status_code == 200:
            # Determine filename
            parsed = urlparse(best_url)
            filename = os.path.basename(parsed.path)
            if not filename or '.' not in filename:
                filename = "pinterest_image.jpg"
                
            out_path = os.path.join(OUTPUT_DIR, filename)
            with open(out_path, 'wb') as f:
                f.write(img_resp.content)
            print(f"Successfully downloaded and saved to {out_path}!")
        else:
            print(f"Failed to download image. Status code: {img_resp.status_code}")
    else:
        print("Could not find any image URLs in the page HTML. Here is a snippet of HTML:")
        print(html[:1000])

if __name__ == "__main__":
    main()
