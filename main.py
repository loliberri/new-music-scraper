import os
import csv
import sys
from time import sleep
from datetime import date

from bbc6_scraper import scrape_bbc6_playlist
from deezer_lookup import search_deezer_track

# Output directory — writes into the repo's output/ folder on GitHub Actions
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
MASTER_NOTE_NAME = "BBC6 All.md"


def append_track_to_master_note(track: dict):
    """
    Append a track to a single master note (BBC6 All) as a table row,
    avoiding duplicates based on artist+title.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, MASTER_NOTE_NAME)

    key = f"{track['artist']}|{track['title']}".lower().strip()

    # If file doesn't exist, create with header
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write("source: BBC Radio 6\n")
            f.write("---\n\n")
            f.write("| Date | Time | Artist | Title | Genre | Deezer Link |\n")
            f.write("| ---- | ---- | ------ | ----- | ----- | ----------- |\n")

    # Read existing lines to avoid duplicates
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

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
        artist = parts[3]
        title = parts[4]
        existing_keys.add(f"{artist}|{title}".lower().strip())

    if key in existing_keys:
        return  # already logged

    today_str = date.today().isoformat()  # e.g. 2026-05-02
    time_str = track.get("time", "")
    artist_str = track.get("artist", "")
    title_str = track.get("title", "")
    genre_str = track.get("genre", "Unknown")
    deezer_link = track.get("deezer_link", "")

    new_row = (
        f"| {today_str} | {time_str} | {artist_str} | {title_str} | "
        f"{genre_str} | {deezer_link} |\n"
    )

    with open(path, "a", encoding="utf-8") as f:
        f.write(new_row)


def run_daily():
    """
    Daily mode: scrape BBC6, look up Deezer, update master note.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_path = os.path.join(OUTPUT_DIR, "bbc6_log.txt")

    with open(log_path, "a", encoding="utf-8") as log:
        log.write("Script started (daily)\n")

    songs = scrape_bbc6_playlist()
    print(f"Scraped {len(songs)} tracks from BBC 6")

    enriched = []

    for idx, song in enumerate(songs, start=1):
        artist = song["artist"]
        title = song["title"]

        print(f"[{idx}/{len(songs)}] Searching on Deezer: {artist} – {title}")
        deezer_info = search_deezer_track(artist, title)

        if deezer_info is None:
            print("  -> No Deezer match found")
            continue

        song_with_deezer = {
            **song,
            "deezer_id": deezer_info["id"],
            "deezer_link": deezer_info["link"],
            "deezer_title": deezer_info["title"],
            "deezer_artist": deezer_info["artist"],
            "genre": deezer_info.get("genre", "Unknown"),
        }

        enriched.append(song_with_deezer)
        append_track_to_master_note(song_with_deezer)

        print(
            f"  -> Found: {deezer_info['artist']} – {deezer_info['title']} "
            f"[{deezer_info.get('genre', 'Unknown')}]"
        )
        print(f"     Link: {deezer_info['link']}")

        sleep(0.3)

    print(f"\nSuccessfully matched {len(enriched)} tracks on Deezer")
    for track in enriched[:10]:
        print(
            f"{track['time']} - {track['artist']} – {track['title']} "
            f"({track.get('genre', 'Unknown')}) -> {track['deezer_link']}"
        )

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"Script finished (daily). Matched {len(enriched)} tracks.\n")


def export_weekly_csv():
    """
    Weekly mode: read BBC6 All.md table and export a CSV named
    'Music - FIRST_DATE.csv', where FIRST_DATE is the earliest date in the table.
    """
    path = os.path.join(OUTPUT_DIR, MASTER_NOTE_NAME)

    if not os.path.exists(path):
        print("Master note does not exist yet; nothing to export.")
        return

    rows = []
    dates = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("| Date"):
                continue
            if not line.startswith("|"):
                continue
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

    if not rows:
        print("No rows found in master note; nothing to export.")
        return

    parsed_dates = []
    for d in dates:
        try:
            parsed_dates.append(date.fromisoformat(d))
        except ValueError:
            continue

    if not parsed_dates:
        print("Could not parse any dates; using 'UnknownDate' in filename.")
        first_date_str = "UnknownDate"
    else:
        first_date = min(parsed_dates)
        first_date_str = first_date.isoformat()

    csv_name = f"Music - {first_date_str}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_name)

    with open(csv_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "time", "artist", "title", "genre", "deezer_link"])
        for r in rows:
            writer.writerow(
                [
                    r["date"],
                    r["time"],
                    r["artist"],
                    r["title"],
                    r["genre"],
                    r["deezer_link"],
                ]
            )

    print(f"Weekly CSV written to: {csv_path}")


if __name__ == "__main__":
    # Usage:
    #   python main.py            -> run daily mode (default)
    #   python main.py weekly     -> export weekly CSV
    if len(sys.argv) > 1 and sys.argv[1].lower() == "weekly":
        export_weekly_csv()
    else:
        run_daily()
