# imports
import os
import sys
from time import sleep
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# importing files
from bbc6_scraper import scrape_bbc6_playlist
from deezer_lookup import search_deezer_track

# creates an output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# markdown file for storing information
MASTER_NOTE_NAME = "BBC6 All.md"


# function to append track to existing table
def append_track_to_master_note(track: dict):

    # check if the file exists in path
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # building file path
    path = os.path.join(OUTPUT_DIR, MASTER_NOTE_NAME)

    # with the following format
    key = f"{track['artist']}|{track['title']}".lower().strip()

    # if the file doesn't exist create a new note with the following headers
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write("source: BBC Radio 6\n")
            f.write("---\n\n")
            f.write("| Date | Time | Artist | Title | Genre | Deezer Link |\n")
            f.write("| ---- | ---- | ------ | ----- | ----- | ----------- |\n")

    # reading existing lines so there are no duplicates
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # creating the table
    existing_keys = set()
    for line in lines:
        if line.startswith("| Date"):
            continue
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        artist = parts[3]
        title = parts[4]
        existing_keys.add(f"{artist}|{title}".lower().strip())

    # skipping duplicates
    if key in existing_keys:
        return

    # adding new information into a new row
    today_str = date.today().isoformat()
    time_str = track.get("time", "")
    artist_str = track.get("artist", "")
    title_str = track.get("title", "")
    genre_str = track.get("genre", "Unknown")
    deezer_link = track.get("deezer_link", "")

    # building the markdown row
    new_row = (
        f"| {today_str} | {time_str} | {artist_str} | {title_str} | "
        f"{genre_str} | {deezer_link} |\n"
    )

    # appending to the file
    with open(path, "a", encoding="utf-8") as f:
        f.write(new_row)


# function to export all data to a formatted Excel file
def export_excel():

    # reading master note
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
            if line.startswith("| ----"):
                continue
            if not line.startswith("|"):
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            date_str   = parts[1]
            time_str   = parts[2]
            artist_str = parts[3]
            title_str  = parts[4]
            genre_str  = parts[5]
            deezer_link = parts[6]

            rows.append({
                "date":        date_str,
                "time":        time_str,
                "artist":      artist_str,
                "title":       title_str,
                "genre":       genre_str,
                "deezer_link": deezer_link,
            })
            dates.append(date_str)

    if not rows:
        print("No rows found in master note; nothing to export.")
        return

    # get earliest date for filename
    parsed_dates = []
    for d in dates:
        try:
            parsed_dates.append(date.fromisoformat(d))
        except ValueError:
            continue

    first_date_str = min(parsed_dates).isoformat() if parsed_dates else "UnknownDate"

    # fixed filename so it gets overwritten/updated each run rather than
    # creating a new file every day
    xlsx_name = "BBC6 Music Log.xlsx"
    xlsx_path = os.path.join(OUTPUT_DIR, xlsx_name)

    # build workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BBC6 Tracks"

    # header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="01696F")  # Teal
    headers = ["Date", "Time", "Artist", "Title", "Genre", "Deezer Link"]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # data rows
    for row_idx, r in enumerate(rows, start=2):
        ws.cell(row=row_idx, column=1, value=r["date"])
        ws.cell(row=row_idx, column=2, value=r["time"])
        ws.cell(row=row_idx, column=3, value=r["artist"])
        ws.cell(row=row_idx, column=4, value=r["title"])
        ws.cell(row=row_idx, column=5, value=r["genre"])
        # make Deezer link clickable
        link = r["deezer_link"]
        cell = ws.cell(row=row_idx, column=6, value=link)
        if link.startswith("http"):
            cell.hyperlink = link
            cell.font = Font(color="0563C1", underline="single")

    # auto-fit column widths
    col_widths = [12, 8, 30, 40, 20, 50]
    for col, width in enumerate(col_widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = width

    # freeze top row
    ws.freeze_panes = "A2"

    wb.save(xlsx_path)
    print(f"Excel file written to: {xlsx_path}")


# function to create daily run
def run_daily():
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
            print(" -> No Deezer match found")
            continue

        song_with_deezer = {
            **song,
            "deezer_id":     deezer_info["id"],
            "deezer_link":   deezer_info["link"],
            "deezer_title":  deezer_info["title"],
            "deezer_artist": deezer_info["artist"],
            "genre":         deezer_info.get("genre", "Unknown"),
        }

        enriched.append(song_with_deezer)
        append_track_to_master_note(song_with_deezer)

        print(
            f" -> Found: {deezer_info['artist']} – {deezer_info['title']} "
            f"[{deezer_info.get('genre', 'Unknown')}]"
        )
        print(f"    Link: {deezer_info['link']}")

        sleep(0.3)

    print(f"\nSuccessfully matched {len(enriched)} tracks on Deezer")
    for track in enriched[:10]:
        print(
            f"{track['time']} - {track['artist']} – {track['title']} "
            f"({track.get('genre', 'Unknown')}) -> {track['deezer_link']}"
        )

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"Script finished (daily). Matched {len(enriched)} tracks.\n")

    # export updated Excel file after every daily run
    export_excel()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "excel":
        export_excel()
    else:
        run_daily()
