import zipfile
import os
import librosa
import numpy as np
from pydub import AudioSegment
import streamlit as st

# Ensure the temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Function to extract segments based on energy
def extract_best_segments(file_path):
    y, sr = librosa.load(file_path)
    energy = librosa.feature.rms(y=y).flatten()
    threshold = np.mean(energy) * 1.5  # Define a threshold for selecting segments
    segments = []

    for i in range(len(energy)):
        if energy[i] > threshold:
            start_time = librosa.frames_to_time(i, sr=sr)
            segments.append(start_time)  # Only save the start times for segments

    return segments

# Function to create a mashup from selected songs
def create_mashup(selected_songs, hype_level, output_file='mashup.mp3'):
    mashup = AudioSegment.silent(duration=0)  # Start with silence
    used_segments = []  # Track used segments

    # Calculate total duration and target segment length
    total_length = sum([AudioSegment.from_file(song).duration_seconds for song in selected_songs])  # Total length of songs
    segment_length = total_length / len(selected_songs) / len(selected_songs) * 1000  # Length of each segment in milliseconds

    for song in selected_songs:
        best_segments = extract_best_segments(song)  # Get the best segments with timings
        
        # Filter out used segments
        available_segments = [seg for seg in best_segments if seg not in used_segments]
        
        # Select segments based on hype level
        num_segments = 3 if hype_level == 'high' else 2 if hype_level == 'medium' else 1
        
        for segment_start in available_segments[:num_segments]:
            start_time = int(segment_start * 1000)  # Convert to milliseconds
            end_time = start_time + int(segment_length)  # Calculate end time based on segment length
            
            # Load audio and extract the segment
            audio_segment = AudioSegment.from_file(song)[start_time:end_time]  # Extract the segment
            
            # Apply beat matching and transitions
            if len(mashup) > 0:  # Check if there's already something in the mashup
                # Use a short fade out and a gradual crossfade for beat matching
                mashup = mashup.fade_out(500)  # Fade out the last segment
                mashup = mashup.append(audio_segment.fade_in(500), crossfade=1500)  # Fade in the new segment over 1.5 seconds
            else:
                mashup += audio_segment.fade_in(500)  # Just fade in the first segment

            # Add the segment to used segments
            used_segments.append(segment_start)

    # Final adjustments for DJ effects without affecting song quality
    # You can add effects like low-pass and high-pass filters here if needed

    mashup.export(output_file, format='mp3')
    return output_file

# Streamlit UI
st.title("DJ Mashup Creator")

# Upload mp3 files
uploaded_files = st.file_uploader("Upload your MP3 files", type=["mp3"], accept_multiple_files=True)

# Select hype level
hype_level = st.selectbox("Select hype level", ["low", "medium", "high"])

if st.button("Create Mashup"):
    if uploaded_files:
        song_paths = []
        for uploaded_file in uploaded_files:
            # Save uploaded file to a temporary directory
            temp_path = os.path.join("temp", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            song_paths.append(temp_path)

        # Create the mashup
        output_file = create_mashup(song_paths, hype_level)

        # Provide download link for the generated mashup
        st.success("Mashup created successfully!")
        with open(output_file, 'rb') as f:
            st.download_button("Download Mashup", f, file_name='mashup.mp3', mime='audio/mp3')

        # Play the mashup in the app
        st.audio(output_file)

    else:
        st.error("Please upload at least one MP3 file.")
