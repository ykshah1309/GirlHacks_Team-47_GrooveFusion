import os
import zipfile
import librosa
import numpy as np
import soundfile as sf
from textblob import TextBlob
import lyricsgenius
import streamlit as st

# Streamlit app setup
st.title('Dynamic Mashup App')
st.write("Upload a zip file of MP3s to create a mashup based on energy levels and lyrics mood.")

# Upload zip file using Streamlit's uploader
uploaded_zip = st.file_uploader("Choose a zip file", type="zip")

# If a file is uploaded, extract and process it
if uploaded_zip:
    # Save the uploaded zip to a temporary directory
    zip_file_path = f"/tmp/{uploaded_zip.name}"
    with open(zip_file_path, "wb") as f:
        f.write(uploaded_zip.getbuffer())

    # Step 1: Extract the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall("/tmp/songs")
        
    # List all MP3 files from the extracted folder
    mp3_files = [f for f in os.listdir("/tmp/songs") if f.endswith('.mp3')]
    st.write(f"Extracted MP3 files: {mp3_files}")

    # Initialize Genius API (add your own API key here)
    GENIUS_API_TOKEN = 'your-genius-api-token'
    genius = lyricsgenius.Genius(GENIUS_API_TOKEN)

    # Function to extract audio features (energy)
    def get_audio_features(file_path):
        y, sr = librosa.load(file_path, sr=None)
        energy = np.mean(librosa.feature.rms(y=y))
        return energy

    # Function to fetch song lyrics using Genius API
    def get_song_lyrics(song_title, artist_name):
        try:
            song = genius.search_song(song_title, artist_name)
            return song.lyrics if song else None
        except Exception as e:
            st.write(f"Error fetching lyrics for {song_title}: {e}")
            return None

    # Function to analyze lyrics mood using TextBlob sentiment analysis
    def analyze_lyrics_mood(lyrics):
        blob = TextBlob(lyrics)
        sentiment = blob.sentiment.polarity
        if sentiment > 0:
            return 'happy'
        elif sentiment < 0:
            return 'sad'
        else:
            return 'neutral'

    # Function to classify songs based on energy and mood
    def classify_by_energy_and_mood(songs, hype_level, target_mood):
        # Define energy ranges corresponding to hype levels
        energy_ranges = {
            1: (0, 0.1),
            2: (0.1, 0.2),
            3: (0.2, 0.3),
            4: (0.3, 0.4),
            5: (0.4, 1.0),
        }
        
        min_energy, max_energy = energy_ranges[hype_level]
        selected_tracks = []
        
        for song in songs:
            file_path = os.path.join("/tmp/songs", song)
            
            # Extract audio features
            energy = get_audio_features(file_path)
            
            # Analyze lyrics and mood
            song_title = song.replace('.mp3', '')  # Assuming song title matches file name
            lyrics = get_song_lyrics(song_title, 'artist')  # Replace 'artist' with actual artist name if available
            
            if lyrics:
                mood = analyze_lyrics_mood(lyrics)
                # Filter songs based on both energy and mood
                if min_energy <= energy <= max_energy and mood == target_mood:
                    selected_tracks.append(song)
        
        return selected_tracks

    # Step 2: User inputs
    hype_level = st.slider("Set Hype Level (1 to 5):", min_value=1, max_value=5)
    mood = st.selectbox("Choose Mood (happy, sad, neutral):", ['happy', 'sad', 'neutral'])

    # Classify songs based on the user input
    filtered_songs = classify_by_energy_and_mood(mp3_files, hype_level, mood)
    st.write(f"Filtered {len(filtered_songs)} songs with Hype Level {hype_level} and Mood {mood}")
    st.write("Songs:", filtered_songs)

    # Step 3: Generate mashup from the filtered songs
    def create_mashup(track_paths, mashup_filename="mashup_output.wav"):
        mashup = None
        for track_path in track_paths:
            y, sr = librosa.load(track_path, sr=None)
            if mashup is None:
                mashup = y
            else:
                mashup = np.concatenate((mashup, y))  # Concatenate audio data
        sf.write(mashup_filename, mashup, sr)
        return mashup_filename

    # If there are filtered songs, generate a mashup from them
    if len(filtered_songs) > 0:
        track_paths = [os.path.join("/tmp/songs", song) for song in filtered_songs[:2]]  # Limit to first 2 tracks for demo
        mashup_filename = create_mashup(track_paths)
        st.success("Mashup created successfully!")
        st.write("File saved as:", mashup_filename)
    else:
        st.write("No songs found with the specified energy level and mood.")
