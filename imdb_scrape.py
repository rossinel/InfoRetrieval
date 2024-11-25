import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from imdb import Cinemagoer
import time

# Function to load all items using Selenium
def fetch_tv_series_with_selenium(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    print("Opening IMDb list...")
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ipc-metadata-list-summary-item")))

    print("Scrolling to load all series...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    print("Finished loading all series.")

    series_titles = []
    for item in soup.find_all('li', class_='ipc-metadata-list-summary-item'):
        title_tag = item.find('a', class_='ipc-title-link-wrapper')
        metadata_tag = item.find('div', class_='sc-6ade9358-6 cBtpuV dli-title-metadata')
        if title_tag and metadata_tag:
            title = title_tag.text.strip()
            imdb_id = title_tag['href'].split('/')[2]
            metadata_text = metadata_tag.text.strip()
            num_episodes = None
            if "eps" in metadata_text:
                parts = metadata_text.split()
                for part in parts:
                    if "eps" in part:
                        num_episodes = part.replace("eps", "").strip()
                        break
            series_titles.append({'title': title, 'imdb_id': imdb_id, 'num_episodes': num_episodes})

    return series_titles

# Function to fetch metadata and insert into SQLite database
def fetch_metadata_and_save_to_db(series_list, db_file):
    ia = Cinemagoer()
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            year INTEGER,
            genres TEXT,
            directors TEXT,
            cast TEXT,
            rating REAL,
            plot TEXT,
            runtime TEXT,
            num_episodes INTEGER
        )
    ''')

    for series in series_list:
        try:
            imdb_id = series['imdb_id']
            show = ia.get_movie(imdb_id[2:])
            metadata = {
                'title': show.get('title'),
                'year': show.get('year'),
                'genres': ', '.join(show.get('genres', [])),
                'directors': ', '.join(person['name'] for person in show.get('directors', [])),
                'cast': ', '.join(person['name'] for person in show.get('cast', [])[:10]),
                'rating': show.get('rating'),
                'plot': show.get('plot outline', ''),
                'runtime': ', '.join(show.get('runtimes', [])),
                'num_episodes': series.get('num_episodes')
            }

            # Insert or replace the data into the database
            cursor.execute('''
                INSERT INTO tv_series (title, year, genres, directors, cast, rating, plot, runtime, num_episodes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title) DO UPDATE SET
                    year=excluded.year,
                    genres=excluded.genres,
                    directors=excluded.directors,
                    cast=excluded.cast,
                    rating=excluded.rating,
                    plot=excluded.plot,
                    runtime=excluded.runtime,
                    num_episodes=excluded.num_episodes
            ''', (
                metadata['title'], metadata['year'], metadata['genres'],
                metadata['directors'], metadata['cast'], metadata['rating'],
                metadata['plot'], metadata['runtime'], metadata['num_episodes']
            ))

            print(f"Saved metadata for: {metadata['title']}")
        except Exception as e:
            print(f"Error fetching metadata for {series['title']}: {e}")
        time.sleep(1)  # Avoid hitting IMDb rate limits

    conn.commit()
    conn.close()

# Main function
def main():
    imdb_list_url = "https://www.imdb.com/list/ls087208947/"
    db_file = "tv_series_metadata.db"

    print("Fetching TV series from IMDb list using Selenium...")
    series_list = fetch_tv_series_with_selenium(imdb_list_url)
    
    if not series_list:
        print("No series found. Exiting.")
        return

    print(f"Found {len(series_list)} series. Fetching metadata and saving to database...")
    fetch_metadata_and_save_to_db(series_list, db_file)
    print(f"Data successfully saved to {db_file}")

if __name__ == "__main__":
    main()
