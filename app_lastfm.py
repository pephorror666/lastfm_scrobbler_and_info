import streamlit as st
import pylast
import time
import os
#from dotenv import load_dotenv

#load_dotenv()  # Load environment variables from .env file

# Initialize session state
if 'network' not in st.session_state:
    st.session_state.network = None
if 'album' not in st.session_state:
    st.session_state.album = None

API_KEY = os.getenv("LASTFM_API_KEY")
API_SECRET = os.getenv("LASTFM_API_SECRET")

def initialize_network(username, password):
    password_hash = pylast.md5(password)
    return pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                                username=username, password_hash=password_hash)

def search_album(network, artist_name, album_name):
    results = network.search_for_album(album_name)
    
    if results:
        albums = results.get_next_page()
        
        if albums:
            closest_match = next((album for album in albums 
                                  if album.artist.name.lower() == artist_name.lower()), 
                                 albums[0])
            
            return closest_match
    return None

def scrobble_album(network, album):
    tracks = album.get_tracks()
    current_time = int(time.time())
    for track in tracks:
        network.scrobble(artist=album.artist.name, title=track.title, timestamp=current_time)
        current_time -= 300  # Subtract 5 minutes for each track
    return f"Scrobbled all tracks from {album.artist.name} - {album.title} to Last.fm"

def show_artist_info(album):
    artist = album.artist
    return f"Artist: {artist.name}\nBio: {artist.get_bio_summary()}"

def show_tracklist(album):
    tracks = [f"- {track.title}" for track in album.get_tracks()]
    return f"Tracklist for {album.artist.name} - {album.title}:\n" + "\n".join(tracks)

def show_similar_artists(album):
    similar = album.artist.get_similar()
    artists = [f"- {artist.name} (similarity: {similarity:.2f})" for artist, similarity in similar[:5]]
    return f"Similar artists to {album.artist.name}:\n" + "\n".join(artists)

st.title("Last.fm Album Scrobbler")

if 'network' not in st.session_state:
    st.subheader("Login to Last.fm")
    username = st.text_input("Enter your Last.fm username:")
    password = st.text_input("Enter your Last.fm password:", type="password")
    
    if st.button("Login"):
        if username and password:
            try:
                network = initialize_network(username, password)
                st.session_state.network = network
                st.success("Login successful!")
            except pylast.WSError:
                st.error("Login failed. Please check your credentials and try again.")
        else:
            st.warning("Please enter both username and password.")

if 'network' in st.session_state:
    artist_name = st.text_input("Enter the artist name:")
    album_name = st.text_input("Enter the album name:")

    if st.button("Search Album"):
        if artist_name and album_name:
            album = search_album(st.session_state.network, artist_name, album_name)
            if album:
                st.session_state.album = album
                st.success(f"Found: {album.artist.name} - {album.title}")
            else:
                st.error("No album found. Please check your input and try again.")
        else:
            st.warning("Please enter both artist name and album name.")

    if 'album' in st.session_state:
        option = st.selectbox(
            "What would you like to do?",
            ("Scrobble to Last.fm", "Show artist information", "Show album tracklist", "Show similar artists")
        )

        if st.button("Execute"):
            if option == "Scrobble to Last.fm":
                result = scrobble_album(st.session_state.network, st.session_state.album)
                st.success(result)
            elif option == "Show artist information":
                info = show_artist_info(st.session_state.album)
                st.info(info)
            elif option == "Show album tracklist":
                tracklist = show_tracklist(st.session_state.album)
                st.text(tracklist)
            elif option == "Show similar artists":
                similar = show_similar_artists(st.session_state.album)
                st.text(similar)
