#imports
import requests

#link to Deezer API
DEEZER_SEARCH_URL = "https://api.deezer.com/search"
DEEZER_ARTIST_URL = "https://api.deezer.com/artist/"

#mapping Deezer genere ID's 
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

}

#creating a function to look up artist and get genre label
def _get_artist_genre(artist_id: int) -> str | None:

    #if no artist, stop early
    if not artist_id:
        return None

    #requesting artist data from Deezer
    resp = requests.get(f"{DEEZER_ARTIST_URL}{artist_id}")

    #if request fails, return none
    if resp.status_code != 200:
        return None

    #converting info into dictionary
    data = resp.json()

    #pulling genre from artist data
    genre_id = data.get("genre_id")

    #if the genre is available, return label i.e. Rock
    if genre_id is not None and genre_id in GENRE_ID_MAP:
        return GENRE_ID_MAP[genre_id]

    #if no genre, return None
    return None

#search Deezer for artist and title and returns a dictionary or none
def search_deezer_track(artist: str, title: str):
    if not title:
        return None

    #search query i.e. artist and title or just title
    if artist:
        query = f'artist:"{artist}" track:"{title}"'
    else:
        query = f'track:"{title}"'

    #send the search request
    params = {"q": query}
    resp = requests.get(DEEZER_SEARCH_URL, params=params)

    #to catch errors
    resp.raise_for_status()

    #parseing results and if missing, defaults to an empty list
    data = resp.json()
    results = data.get("data", [])

    #if nothing found, return None
    if not results:
        return None

    #assumes the first track is the right one
    track = results[0]

    #getting track details
    track_id = track.get("id")
    track_title = track.get("title")
    track_artist_obj = track.get("artist") or {}
    track_artist = track_artist_obj.get("name")
    track_artist_id = track_artist_obj.get("id")
    track_link = track.get("link")

    #discard results if critcal information is missing
    if not (track_id and track_link):
        return None

    #get the genre of the artist
    genre = _get_artist_genre(track_artist_id) or "Unknown"

    #retuns a structured results within a dictionary
    return {
        "id": track_id,
        "title": track_title,
        "artist": track_artist,
        "link": track_link,
        "genre": genre,
        "raw": track,
    }

#only runs if executed directly
if __name__ == "__main__":
    result = search_deezer_track("R.E.M.", "Losing My Religion")
    print(result)
