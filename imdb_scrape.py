from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
import time

# Function to scrape all episodes for a given season URL
def scrape_episodes_from_season(season_url, db_file, show_name):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    print(f"Opening season URL: {season_url}")
    driver.get(season_url)

    # Wait for episodes to load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "episode-item-wrapper")))

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show TEXT,
            season INTEGER,
            episode INTEGER,
            episode_title TEXT,
            air_date TEXT,
            rating REAL,
            votes INTEGER,
            plot TEXT
        )
    ''')

    # Extract episodes
    episodes = soup.find_all('article', class_='sc-f8507e90-1 cHtpvn episode-item-wrapper')
    for episode in episodes:
        # Extract episode metadata
        episode_title_tag = episode.find('div', class_='ipc-title__text')
        episode_title = episode_title_tag.text.strip() if episode_title_tag else "N/A"

        air_date_tag = episode.find('span', class_='sc-f2169d65-10 bYaARM')
        air_date = air_date_tag.text.strip() if air_date_tag else "N/A"

        rating_tag = episode.find('span', class_='ipc-rating-star--rating')
        rating = float(rating_tag.text.strip()) if rating_tag else None

        votes_tag = episode.find('span', class_='ipc-rating-star--voteCount')
        votes = float(votes_tag.text.replace('(', '').replace(')', '').replace('K', '000').strip()) if votes_tag else None

        plot_tag = episode.find('div', class_='ipc-html-content-inner-div')
        plot = plot_tag.text.strip() if plot_tag else "N/A"

        # Parse season and episode numbers
        episode_info = episode_title.split('∙')[0].strip() if '∙' in episode_title else "S0.E0"
        season, episode_number = map(int, episode_info.replace('S', '').replace('E', '').split('.'))

        # Insert into SQLite database
        cursor.execute('''
            INSERT INTO episodes (show, season, episode, episode_title, air_date, rating, votes, plot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (show_name, season, episode_number, episode_title, air_date, rating, votes, plot))

        print(f"Scraped: Season {season}, Episode {episode_number}: {episode_title}")

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print(f"Finished scraping season from {season_url}")

# Function to scrape all seasons for a given show
def scrape_all_seasons(base_url, num_seasons, db_file, show_name):
    for season in range(1, num_seasons + 1):
        season_url = f"{base_url}?season={season}"
        scrape_episodes_from_season(season_url, db_file, show_name)
        time.sleep(2)  # Avoid hitting IMDb's rate limit

# Main function
def main():
    # base_url = "https://www.imdb.com/title/tt0182576/episodes/"  # Family Guy
    # base_url = "https://www.imdb.com/title/tt0121955/episodes/"  # South Park
    # base_url = "https://www.imdb.com/title/tt0096697/episodes/"  # The Simpsons
    shows = {
        "Family Guy": {"link":"https://www.imdb.com/title/tt0182576/episodes/", "seasons": 23},
        "South Park": {"link":"https://www.imdb.com/title/tt0121955/episodes/", "seasons": 30},
        "The Simpsons": {"link":"https://www.imdb.com/title/tt0096697/episodes/", "seasons": 36}
    }
    db_file = "episodes.db"

    for show_name, show_data in shows.items():
        link = show_data["link"]
        num_seasons = show_data["seasons"]
        print(f"Starting to scrape all seasons for {show_name}...")
        scrape_all_seasons(link, num_seasons, db_file, show_name)
        print(f"All seasons have been scraped and saved to {db_file}")
        

if __name__ == "__main__":
    main()
