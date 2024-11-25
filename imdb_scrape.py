from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from imdb import Cinemagoer
import json
import time

# Function to load all items using Selenium
def fetch_tv_series_with_selenium(url):
    # Set up Selenium WebDriver with custom User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={user_agent}")  # Add custom User-Agent
    driver = webdriver.Chrome(options=options)

    print("Opening IMDb list...")
    driver.get(url)

    # Wait for the page to load initially
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ipc-metadata-list-summary-item")))

    # Scroll and load all items
    print("Scrolling to load all series...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new content to load

        # Check if more content has been loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Exit loop when no new content is loaded
        last_height = new_height

    # Get the full page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    print("Finished loading all series.")

    # Extract TV series from the loaded page
    series_titles = []
    for item in soup.find_all('li', class_='ipc-metadata-list-summary-item'):
        title_tag = item.find('a', class_='ipc-title-link-wrapper')
        metadata_tag = item.find('div', class_='sc-6ade9358-6 cBtpuV dli-title-metadata')
        if title_tag and metadata_tag:
            title = title_tag.text.strip()
            imdb_id = title_tag['href'].split('/')[2]  # Extract ID from the URL
            
            # Parse metadata for number of episodes
            metadata_text = metadata_tag.text.strip()
            num_episodes = None
            if "eps" in metadata_text:
                parts = metadata_text.split()
                num_episodes = parts[0][9:]
                
            
            series_titles.append({'title': title, 'imdb_id': imdb_id, 'num_episodes': num_episodes})

    return series_titles

# Function to fetch metadata for each series using Cinemagoer
def fetch_metadata_with_cinemagoer(series_list):
    ia = Cinemagoer()
    series_metadata = []

    for series in series_list:
        try:
            imdb_id = series['imdb_id']
            show = ia.get_movie(imdb_id[2:])  # Remove "tt" prefix for Cinemagoer
            metadata = {
                'title': show.get('title'),
                'year': show.get('year'),
                'genres': show.get('genres', []),
                'directors': [person['name'] for person in show.get('directors', [])],
                'cast': [person['name'] for person in show.get('cast', [])[:10]],  # Limit to top 10 cast members
                'rating': show.get('rating'),
                'plot': show.get('plot outline', ''),
                'runtime': show.get('runtimes', []),
                'num_episodes': series['num_episodes']  # Include number of episodes
            }
            series_metadata.append(metadata)
            print(f"Fetched metadata for: {metadata['title']}")
        except Exception as e:
            print(f"Error fetching metadata for {series['title']}: {e}")
        time.sleep(1)  # To avoid hitting IMDB API rate limits

    return series_metadata

# Main function
def main():
    imdb_list_url = "https://www.imdb.com/list/ls087208947/"
    print("Fetching TV series from IMDb list using Selenium...")
    series_list = fetch_tv_series_with_selenium(imdb_list_url)
    
    if not series_list:
        print("No series found. Exiting.")
        return

    print(f"Found {len(series_list)} series. Fetching metadata...")
    metadata = fetch_metadata_with_cinemagoer(series_list)
    
    # Save metadata to a JSON file
    with open('tv_series_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    print("Metadata collection complete. Saved to 'tv_series_metadata.json'.")

if __name__ == "__main__":
    main()
