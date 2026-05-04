import os
import csv
from time import sleep
from datetime import date

from bbc6_scraper import scrape_bbc6_playlist
from deezer_lookup import search_deezer_track

# Adjust this to your real vault path:
VAULT_ROOT = r"C:\Users\becca\Documents\Brain Farts\Becca's Personal Shit\Music"
MASTER_NOTE_NAME = "BBC6 All.md"


def append_track_to_master_note(track: dict):
    """
    Append a track to a single master note (BBC6 All) as a table row,
    avoiding duplicates based on artist+title.
    """
    music_dir = os.path.join(VAULT_ROOT, "Music")
    os.makedirs(music_dir, exist_ok=True)

    path = os.path.join(music_dir, MASTER_NOTE_NAME)

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


def main():
    # Simple log to see if this script is running and where it's writing
    music_dir = os.path.join(VAULT_ROOT, "Music")
    os.makedirs(music_dir, exist_ok=True)
    log_path = os.path.join(music_dir, "bbc6_log.txt")

    with open(log_path, "a", encoding="utf-8") as log:
        log.write("Script started\n")

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

        # Small pause to avoid hammering the API
        sleep(0.3)

    print(f"\nSuccessfully matched {len(enriched)} tracks on Deezer")
    for track in enriched[:10]:
        print(
            f"{track['time']} - {track['artist']} – {track['title']} "
            f"({track.get('genre', 'Unknown')}) -> {track['deezer_link']}"
        )

    # Write/update CSV with all enriched tracks
    csv_path = os.path.join(music_dir, "bbc6_all.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # header
        writer.writerow(["date", "time", "artist", "title", "genre", "deezer_link"])
        # rows
        today_str = date.today().isoformat()
        for track in enriched:
            writer.writerow([
                today_str,
                track.get("time", ""),
                track.get("artist", ""),
                track.get("title", ""),
                track.get("genre", "Unknown"),
                track.get("deezer_link", ""),
            ])

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"Script finished. Matched {len(enriched)} tracks.\n")


if __name__ == "__main__":
    main()