import zipfile
import os
import librosa
import numpy as np
from pydub import AudioSegment

# Step 1: Unzip the MP3 files
zip_path = '/content/beyonce-drunk-in-love-audio-70k (2).zip'  # Change this to your zip file path
#extract_path_1 = '/content/extracted_songs'''
extract_path = '/content/extracted_songs/beyonce-drunk-in-love-audio-70k'

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

# List extracted files
mp3_files = [f for f in os.listdir(extract_path) if f.endswith('.mp3')]
print(f'Extracted {len(mp3_files)} MP3 files.')

# Step 2: Extract audio features
def extract_audio_features(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    energy = np.mean(librosa.feature.rms(y=y))  # Average energy
    return tempo, energy

# Step 3: Collect features for each song
features = {}
for file_name in mp3_files:
    file_path = os.path.join(extract_path, file_name)
    tempo, energy = extract_audio_features(file_path)
    features[file_name] = {'tempo': tempo, 'energy': energy}

# Step 4: Rank songs based on a simple score
for file_name, data in features.items():
    # Create a liveliness score based on tempo and energy
    liveliness_score = data['tempo'] + (data['energy'] * 10)  # Adjust weights as necessary
    features[file_name]['liveliness'] = liveliness_score

# Sort songs by liveliness score
ranked_songs = sorted(features.items(), key=lambda x: x[1]['liveliness'], reverse=True)

# Step 5: Create a mashup based on hype level
def create_mashup(selected_songs, output_file='mashup.mp3'):
    mashup = AudioSegment.silent(duration=0)  # Start with silence
    for song in selected_songs:
        song_path = os.path.join(extract_path, song)
        audio = AudioSegment.from_file(song_path)
        mashup += audio  # Concatenate songs
    mashup.export(output_file, format='mp3')
    print(f'Mashup created: {output_file}')

# Determine songs based on hype level
def get_songs_based_on_hype(hype_level):
    if hype_level == 'low':
        return [song[0] for song in ranked_songs[-5:]]  # Last 5 songs
    elif hype_level == 'medium':
        return [song[0] for song in ranked_songs[len(ranked_songs)//4:3*len(ranked_songs)//4]]
    elif hype_level == 'high':
        return [song[0] for song in ranked_songs[:5]]  # Top 5 songs
    else:
        print("Invalid hype level. Please choose from 'low', 'medium', or 'high'.")
        return []

# Example usage
hype_level = 'high'  # Change this to 'low', 'medium', or 'high'
selected_songs = get_songs_based_on_hype(hype_level)
create_mashup(selected_songs)
