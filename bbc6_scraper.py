#imports
import requests
from bs4 import BeautifulSoup

#link to music listings
BBC6_URL = "https://onlineradiobox.com/uk/bbcradio6/playlist/"

#function to scrape information
def scrape_bbc6_playlist():
    """
    Scrape the BBC Radio 6 playlist from OnlineRadioBox.
    Returns a list of dicts: {"title": ..., "artist": ..., "time": ...}.
    """

    #sends a HTML get request to website
    resp = requests.get(BBC6_URL)

    #raises an error if the request has failed
    resp.raise_for_status()

    #gives raw HTML as a string
    html = resp.text

    #parses the HTML
    soup = BeautifulSoup(html, "html.parser")

    #creates an empty list to store tracks
    tracks = []

    #format of table is as follows: 
    # | time | "Artist - Title" |
    #loop through each table row on the website
    for row in soup.select("table tr"):

        #find all table cells in that row
        cells = row.find_all("td")

        #2 cells are expected, if not, skip
        if len(cells) != 2:
            continue  # skip header or weird rows

        #assign time to the 1st cell
        time_cell = cells[0]

        #assign time to the 2nd cell
        info_cell = cells[1]

        #extract info and exclude whitespace
        time_text = time_cell.get_text(strip=True)
        info_text = info_cell.get_text(strip=True)

        #if the cell is empty, ignore it
        if not time_text or not info_text:
            continue

        #info_text typically looks like "Artist - Song Title"
        #split on the first " - " dash.
        if " - " in info_text:
            artist_text, title_text = info_text.split(" - ", 1)
        else:
            #if no - then leave artist blank
            artist_text = ""
            title_text = info_text

        #cleaning up whitespace
        artist_text = artist_text.strip()
        title_text = title_text.strip()

        #if title is empty, skip that row
        if not title_text:
            continue

        #store the information in a dictonary
        tracks.append(
            {
                "title": title_text,
                "artist": artist_text,
                "time": time_text,
            }
        )

    #gives the full list of tracks
    return tracks

#only run if executed directly
if __name__ == "__main__":

    #run the program
    songs = scrape_bbc6_playlist()

    #print how many tracks were scraped
    print(f"Found {len(songs)} tracks")

    #prints the first 20 tracks
    for song in songs[:20]:
        print(f"{song['time']} - {song['artist']} – {song['title']}")
