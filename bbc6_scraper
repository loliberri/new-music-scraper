import requests
from bs4 import BeautifulSoup

# Link to music listings
BBC6_URL = "https://onlineradiobox.com/uk/bbcradio6/playlist/"


def scrape_bbc6_playlist():
    """
    Scrape the BBC Radio 6 playlist from OnlineRadioBox.
    Returns a list of dicts: {"title": ..., "artist": ..., "time": ...}.
    """

    # Sends a HTML get request to website
    resp = requests.get(BBC6_URL)

    # Raises an error if the request has failed
    resp.raise_for_status()

    # Gives raw HTML as a string
    html = resp.text

    # Parses the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Creates an empty list to store tracks
    tracks = []

    # Format of table is as follows:
    # | time | "Artist - Title" |
    # Loop through each table row on the website
    for row in soup.select("table tr"):

        # Find all table cells in that row
        cells = row.find_all("td")

        # 2 cells are expected, if not, skip
        if len(cells) != 2:
            continue  # skip header or weird rows

        # Assign time to the 1st cell
        time_cell = cells[0]

        # Assign info to the 2nd cell
        info_cell = cells[1]

        # Extract info and exclude whitespace
        time_text = time_cell.get_text(strip=True)
        info_text = info_cell.get_text(strip=True)

        # If the cell is empty, ignore it
        if not time_text or not info_text:
            continue

        # info_text typically looks like "Artist - Song Title"
        # Split on the first " - " dash.
        if " - " in info_text:
            artist_text, title_text = info_text.split(" - ", 1)
        else:
            # If no - then leave artist blank
            artist_text = ""
            title_text = info_text

        # Cleaning up whitespace
        artist_text = artist_text.strip()
        title_text = title_text.strip()

        # If title is empty, skip that row
        if not title_text:
            continue

        # Store the information in a dictionary
        tracks.append(
            {
                "title": title_text,
                "artist": artist_text,
                "time": time_text,
            }
        )

    # Return the full list of tracks
    return tracks


# Only run if executed directly
if __name__ == "__main__":

    # Run the program
    songs = scrape_bbc6_playlist()

    # Print how many tracks were scraped
    print(f"Found {len(songs)} tracks")

    # Print the first 20 tracks
    for song in songs[:20]:
        print(f"{song['time']} - {song['artist']} – {song['title']}")
