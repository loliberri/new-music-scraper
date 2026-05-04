import requests

DEEZER_SEARCH_URL = "https://api.deezer.com/search"
DEEZER_ARTIST_URL = "https://api.deezer.com/artist/"

# Simple mapping of Deezer genre IDs to friendly labels.
# You can expand/refine this over time.
GENRE_ID_MAP = {
    132: "Pop",
    116: "Rap/Hip Hop",
    152: "Rock",
    113: "Dance/Electronic",
    165: "Alternative/Indie",
    85:  "Jazz",
    129: "Soul & Funk",
    106: "Soundtrack",
    98:  "Classical",
    # Fallback for anything else you might discover later
}

def _get_artist_genre(artist_id: int) -> str | None:
    """
    Look up the artist on Deezer and try to get a main genre label.
    """
    if not artist_id:
        return None

    resp = requests.get(f"{DEEZER_ARTIST_URL}{artist_id}")
    if resp.status_code != 200:
        return None

    data = resp.json()

    # Some Deezer clients expose a 'genre_id' or similar identifier for the artist.
    genre_id = data.get("genre_id")
    if genre_id is not None and genre_id in GENRE_ID_MAP:
        return GENRE_ID_MAP[genre_id]

    # If no known genre_id, you can fallback to a generic label or None
    return None

def search_deezer_track(artist: str, title: str):
    """
    Search Deezer for a track by artist and title.
    Returns a dict with: {"id", "title", "artist", "link", "genre"} or None if not found.
    """
    if not title:
        return None

    # Build a search query. Include artist if we have it.
    if artist:
        query = f'artist:"{artist}" track:"{title}"'
    else:
        query = f'track:"{title}"'

    params = {"q": query}
    resp = requests.get(DEEZER_SEARCH_URL, params=params)
    resp.raise_for_status()

    data = resp.json()
    results = data.get("data", [])

    if not results:
        return None

    track = results[0]

    track_id = track.get("id")
    track_title = track.get("title")
    track_artist_obj = track.get("artist") or {}
    track_artist = track_artist_obj.get("name")
    track_artist_id = track_artist_obj.get("id")
    track_link = track.get("link")

    if not (track_id and track_link):
        return None

    # Try to determine genre via the artist
    genre = _get_artist_genre(track_artist_id) or "Unknown"

    return {
        "id": track_id,
        "title": track_title,
        "artist": track_artist,
        "link": track_link,
        "genre": genre,
        "raw": track,
    }

if __name__ == "__main__":
    result = search_deezer_track("R.E.M.", "Losing My Religion")
    print(result)