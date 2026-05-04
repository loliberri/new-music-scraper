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

    # Parses the HTML
    soup = BeautifulSoup(resp.text, "html.parser")

    # Creates an empty list to store tracks
    tracks = []

    # Loop through each table row on the website
    for row in soup.select("table tr"):

        # Find all table cells in that row
        cells = row.find_all("td")

        # 2 cells are expected, if not, skip
        if len(cells) != 2:
            continue

        time_text = cells[0].get_text(strip=True)
        info_text = cells[1].get_text(strip=True)

        # If the cell is empty, ignore it
        if not time_text or not info_text:
            continue

        # info_text typically looks like "Artist - Song Title"
        if " - " in info_text:
            artist_text, title_text = info_text.split(" - ", 1)
        else:
            artist_text = ""
            title_text = info_text

        artist_text = artist_text.strip()
        title_text = title_text.strip()

        # If title is empty, skip that row
        if not title_text:
            continue

        tracks.append(
            {
                "title": title_text,
                "artist": artist_text,
                "time": time_text,
            }
        )

    return tracks


if __name__ == "__main__":
    songs = scrape_bbc6_playlist()
    print(f"Found {len(songs)} tracks")
    for song in songs[:20]:
        print(f"{song['time']} - {song['artist']} – {song['title']}")
EOF
echo "Done"
