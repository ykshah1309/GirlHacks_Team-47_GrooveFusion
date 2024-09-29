import zipfile
import os
import librosa
import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from scipy.signal import butter, lfilter
import streamlit as st

# Ensure the temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Function to apply a low-pass filter
def low_pass_filter(audio_segment, cutoff=2000):
    samples = np.array(audio_segment.get_array_of_samples())
    b, a = butter(5, cutoff / (audio_segment.frame_rate / 2), btype='low')
    filtered_samples = lfilter(b, a, samples)
    return AudioSegment(
        filtered_samples.astype(np.int16).tobytes(),
        frame_rate=audio_segment.frame_rate,
        sample_width=audio_segment.sample_width,
        channels=audio_segment.channels
    )

# Function to apply a high-pass filter
def high_pass_filter(audio_segment, cutoff=2000):
    samples = np.array(audio_segment.get_array_of_samples())
    b, a = butter(5, cutoff / (audio_segment.frame_rate / 2), btype='high')
    filtered_samples = lfilter(b, a, samples)
    return AudioSegment(
        filtered_samples.astype(np.int16).tobytes(),
        frame_rate=audio_segment.frame_rate,
        sample_width=audio_segment.sample_width,
        channels=audio_segment.channels
    )

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

    # Calculate total duration and target segment length
    total_length = sum([AudioSegment.from_file(song).duration_seconds for song in selected_songs])  # Total length of songs
    segment_length = total_length / len(selected_songs) / len(selected_songs) * 1000  # Length of each segment in milliseconds

    for song in selected_songs:
        best_segments = extract_best_segments(song)  # Get the best segments with timings

        # Select segments based on hype level
        num_segments = 3 if hype_level == 'high' else 2 if hype_level == 'medium' else 1
        
        for segment_start in best_segments[:num_segments]:
            start_time = int(segment_start * 1000)  # Convert to milliseconds
            end_time = start_time + int(segment_length)  # Calculate end time based on segment length
            
            # Load audio and extract the segment
            audio_segment = AudioSegment.from_file(song)[start_time:end_time]  # Extract the segment

            # Apply effects based on hype level
            if hype_level == 'high':
                audio_segment = audio_segment + audio_segment.fade_in(2000).fade_out(2000)  # Add fade in/out
                audio_segment = low_pass_filter(audio_segment)  # Apply low-pass filter
            elif hype_level == 'medium':
                audio_segment = high_pass_filter(audio_segment)  # Apply high-pass filter
            
            # Apply fade in and fade out effects for smoother transitions
            if len(mashup) > 0:  # Check if there's already something in the mashup
                mashup = mashup.fade_out(500)  # Fade out the last segment
                mashup = mashup.append(audio_segment.fade_in(500), crossfade=1000)  # Fade in the new segment with crossfade
            else:
                mashup += audio_segment.fade_in(500)  # Just fade in the first segment

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
