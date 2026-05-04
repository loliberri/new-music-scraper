import requests
from bs4 import BeautifulSoup

BBC6_URL = "https://onlineradiobox.com/uk/bbcradio6/playlist/"

def scrape_bbc6_playlist():
    """
    Scrape the BBC Radio 6 playlist from OnlineRadioBox.
    Returns a list of dicts: {"title": ..., "artist": ..., "time": ...}.
    """
    resp = requests.get(BBC6_URL)
    resp.raise_for_status()

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    tracks = []

    # The playlist is rendered as a table where each row has:
    # | time | "Artist - Title" |
    # So we look for table rows and then parse the two cells.
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue  # skip header or weird rows

        time_cell = cells[0]
        info_cell = cells[1]

        time_text = time_cell.get_text(strip=True)
        info_text = info_cell.get_text(strip=True)

        if not time_text or not info_text:
            continue

        # info_text typically looks like "Artist - Song Title"
        # Split on the first " - " dash.
        if " - " in info_text:
            artist_text, title_text = info_text.split(" - ", 1)
        else:
            # Fallback: treat the whole thing as title
            artist_text = ""
            title_text = info_text

        artist_text = artist_text.strip()
        title_text = title_text.strip()

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