#imports 
import os
import csv
import sys
from time import sleep
from datetime import date
import openpyxl

#importing files
from bbc6_scraper import scrape_bbc6_playlist
from deezer_lookup import search_deezer_track

#creates an output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

#markdown file for storing information
MASTER_NOTE_NAME = "BBC6 All.md"

#function to append track to exisiting table
def append_track_to_master_note(track: dict):

    #check if the file exists in path
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    #building filing path
    path = os.path.join(OUTPUT_DIR, MASTER_NOTE_NAME)

    #with the following format
    key = f"{track['artist']}|{track['title']}".lower().strip()

    #if the file doesn't exist create a new note with the following headers
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write("source: BBC Radio 6\n")
            f.write("---\n\n")
            f.write("| Date | Time | Artist | Title | Genre | Deezer Link |\n")
            f.write("| ---- | ---- | ------ | ----- | ----- | ----------- |\n")

    #reading existing lines so there are no duplicates
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    #creating the table
    existing_keys = set()
    for line in lines:
        if line.startswith("| Date"):
            continue
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        # ['', Date, Time, Artist, Title, Genre, Deezer Link, '']
        if len(parts) < 6:
            continue

        #extracting artist and the title
        artist = parts[3]
        title = parts[4]
        existing_keys.add(f"{artist}|{title}".lower().strip())

    #skipping duplicates
    if key in existing_keys:
        return  # already logged

    #adding new information into a new row
    today_str = date.today().isoformat()  # e.g. 2026-05-02
    time_str = track.get("time", "")
    artist_str = track.get("artist", "")
    title_str = track.get("title", "")
    genre_str = track.get("genre", "Unknown")
    deezer_link = track.get("deezer_link", "")

    #building the markdown row
    new_row = (
        f"| {today_str} | {time_str} | {artist_str} | {title_str} | "
        f"{genre_str} | {deezer_link} |\n"
    )

    #appending to the file
    with open(path, "a", encoding="utf-8") as f:
        f.write(new_row)

#function to create daily run, check website and deezer and add to master note
def run_daily():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    #log executed file in txt file
    log_path = os.path.join(OUTPUT_DIR, "bbc6_log.txt")

    #in the log, give a start date
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("Script started (daily)\n")

    #scraping songs
    songs = scrape_bbc6_playlist()

    #returns how many were scraped from website
    print(f"Scraped {len(songs)} tracks from BBC 6")

    #creating list to add Deezer details along with link to song
    enriched = []

    #based on the song information, look up the artist and the title of the song
    for idx, song in enumerate(songs, start=1):
        artist = song["artist"]
        title = song["title"]

        #status update
        print(f"[{idx}/{len(songs)}] Searching on Deezer: {artist} – {title}")

        #use the search Deezer function to search Deezer for information
        deezer_info = search_deezer_track(artist, title)

        #if there is no match, return text
        if deezer_info is None:
            print("  -> No Deezer match found")
            continue

        #if there is a match, get this information
        song_with_deezer = {
            **song,
            "deezer_id": deezer_info["id"],
            "deezer_link": deezer_info["link"],
            "deezer_title": deezer_info["title"],
            "deezer_artist": deezer_info["artist"],
            "genre": deezer_info.get("genre", "Unknown"),
        }

        #append it to the list
        enriched.append(song_with_deezer)

        #append information to the master note
        append_track_to_master_note(song_with_deezer)

        #print status
        print(
            f"  -> Found: {deezer_info['artist']} – {deezer_info['title']} "
            f"[{deezer_info.get('genre', 'Unknown')}]"
        )
        print(f"     Link: {deezer_info['link']}")

        #rate limiting
        sleep(0.3)

    #print status
    print(f"\nSuccessfully matched {len(enriched)} tracks on Deezer")
    for track in enriched[:10]:
        print(
            f"{track['time']} - {track['artist']} – {track['title']} "
            f"({track.get('genre', 'Unknown')}) -> {track['deezer_link']}"
        )

    #log final entry
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"Script finished (daily). Matched {len(enriched)} tracks.\n")

#function to export info to csv file on a weekly basis
def export_weekly_csv():

    #reading master note
    path = os.path.join(OUTPUT_DIR, MASTER_NOTE_NAME)

    #if there is nothing on the master note, return text
    if not os.path.exists(path):
        print("Master note does not exist yet; nothing to export.")
        return

    #creating a dictionary for rows and dates
    rows = []
    dates = []

    #deliminating information in table for information that can be used in csv
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("| Date"):
                continue
            if not line.startswith("|"):
                continue

            #split into columns
            parts = [p.strip() for p in line.split("|")]
            # ['', Date, Time, Artist, Title, Genre, Deezer Link, '']
            if len(parts) < 7:
                continue
            date_str = parts[1]
            time_str = parts[2]
            artist_str = parts[3]
            title_str = parts[4]
            genre_str = parts[5]
            deezer_link = parts[6]

            #store rows
            rows.append(
                {
                    "date": date_str,
                    "time": time_str,
                    "artist": artist_str,
                    "title": title_str,
                    "genre": genre_str,
                    "deezer_link": deezer_link,
                }
            )
            dates.append(date_str)

    #if no information, return note
    if not rows:
        print("No rows found in master note; nothing to export.")
        return

    #parsing information
    parsed_dates = []
    for d in dates:
        try:
            parsed_dates.append(date.fromisoformat(d))
        except ValueError:
            continue

    #if there is no date on table, send back text
    if not parsed_dates:
        print("Could not parse any dates; using 'UnknownDate' in filename.")
        first_date_str = "UnknownDate"

    #if dates match, look at the last date that was parsed
    else:
        first_date = min(parsed_dates)
        first_date_str = first_date.isoformat()

    #creating csv 
    csv_name = f"Music - {first_date_str}.csv"

    #sending csv
    csv_path = os.path.join(OUTPUT_DIR, csv_name)

    #creating csv
    xlsx_name = f"Music - {first_date_str}.xlsx"
    xlsx_path = os.path.join(OUTPUT_DIR, xlsx_name)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "time", "artist", "title", "genre", "deezer_link"])
    for r in rows:
        ws.append([r["date"], r["time"], r["artist"], r["title"], r["genre"], r["deezer_link"]])
    wb.save(xlsx_path)
    print(f"Excel file written to: {xlsx_path}")

#instruction to run once weekly, otherwise run daily
if __name__ == "__main__":
    # Usage:
    #   python main.py            -> run daily mode (default)
    #   python main.py weekly     -> export weekly CSV
    if len(sys.argv) > 1 and sys.argv[1].lower() == "weekly":
        export_weekly_csv()
    else:
        run_daily()
