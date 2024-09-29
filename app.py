import zipfile
import os
import librosa
import numpy as np
from pydub import AudioSegment
import streamlit as st
import base64

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
    mashup.export(output_file, format='mp3')
    return output_file

# Streamlit UI with disco theme
st.set_page_config(page_title="DJ Mashup Creator", page_icon="🎵", layout="centered")

# Function to encode the image to base64
def get_base64_image(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert the image located at /content/Purple and Pink Neon Party Virtual Invitation.png to Base64
base64_img = get_base64_image("/content/Purple and Pink Neon Party Virtual Invitation.png")

# Add background styling with club lights and base64 image
page_bg_img = f'''
<style>
body {{
    background-image: url("data:image/png;base64,{base64_img}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

.club-lights {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 100px;
    background: linear-gradient(45deg, rgba(255,0,150,0.8), rgba(0, 255, 255, 0.8), rgba(0, 255, 0, 0.8), rgba(255,255,0,0.8));
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes pulse {{
    0% {{ opacity: 1; }}
    50% {{ opacity: 0.6; }}
    100% {{ opacity: 1; }}
}}
</style>
'''

# Add the club lights HTML
club_lights_html = '''
<div class="club-lights"></div>
'''

# Injecting background and elements into the app
st.markdown(page_bg_img, unsafe_allow_html=True)
st.markdown(club_lights_html, unsafe_allow_html=True)

st.title("🕺 Disco DJ Mashup Creator 💃")
st.markdown("<h2 style='color: hotpink;'>Create your own party mashup!</h2>", unsafe_allow_html=True)

# Upload mp3 files
uploaded_files = st.file_uploader("Upload your MP3 files", type=["mp3"], accept_multiple_files=True)

# Select hype level with a slider
hype_level = st.slider("Adjust the Hype Level 🕺", min_value=1, max_value=3, value=2, format="%d", help="1: Low, 2: Medium, 3: High")

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
        output_file = create_mashup(song_paths, "high" if hype_level == 3 else "medium" if hype_level == 2 else "low")

        # Provide download link for the generated mashup
        st.success("Mashup created successfully!")
        with open(output_file, 'rb') as f:
            st.download_button("Download Mashup", f, file_name='mashup.mp3', mime='audio/mp3')

        # Play the mashup in the app
        st.audio(output_file)

    else:
        st.error("Please upload at least one MP3 file.")
