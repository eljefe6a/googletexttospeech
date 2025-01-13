"""Synthesizes speech from the input string of text or ssml.
Make sure to be working in a virtual environment.

Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from google.cloud import texttospeech
from pydub import AudioSegment
import io
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON, COMM
from mutagen.mp4 import MP4, MP4Cover

# Instantiates a client
client = texttospeech.TextToSpeechClient()

import os

# Iterate through all txt files in book_chapters directory
for filename in sorted(os.listdir("book_chapters")):
    if filename.endswith(".txt"):
        # Check if corresponding MP3 file already exists
        m4a_filename = os.path.splitext(filename)[0] + ".m4a"
        m4a_path = os.path.join("book_chapters", m4a_filename)
        if os.path.exists(m4a_path):
            print(f"Skipping {filename} - M4A already exists")
            continue

                
        # Extract chapter number from filename and convert to integer
        chapter_num = str(int(''.join(filter(str.isdigit, filename))))
        
        # Get the text after the chapter number up to the period
        chapter_text = filename[filename.index(chapter_num) + len(chapter_num) + 1:filename.index('.')]
        chapter_title = f"Chapter {chapter_num}: {chapter_text}"
        author = "TODO"
        album = "TODO"
        
        # Read the chapter text
        chapter_path = os.path.join("book_chapters", filename)
        with open(chapter_path, "r", encoding="utf-8") as f:
            chapter_text = f.read()


        chapter_text = album + " by " + author + ". " + chapter_text

        # Break chapter into chunks of max 5000 chars, splitting on paragraphs
        chunks = []
        current_chunk = ""
        
        # Split into paragraphs by punctuation followed by newline
        paragraphs = [p.strip() for p in chapter_text.replace('.\n', '.|').replace('!\n', '!|').replace('?\n', '?|').split('|') if p.strip()]
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed 5000 chars
            if len(current_chunk) + len(paragraph) > 4500:
                # Store current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    
        # Add final chunk if not empty
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Initialize empty AudioSegment for this chapter with 1 second of silence
        chapter_audio = AudioSegment.silent(duration=1000)

        for chunk in chunks:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=chunk)

            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Studio-O",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )

            # Request uncompressed audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # Uncompressed WAV
                speaking_rate=0.85,
                pitch=0.0,
                volume_gain_db=0.0,
                sample_rate_hertz=24000,
                effects_profile_id=["large-home-entertainment-class-device"]
            )

            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Convert response bytes to AudioSegment
            chunk_audio = AudioSegment.from_wav(io.BytesIO(response.audio_content))
            
            # Add 500ms silence between chunks if not first chunk
            if len(chapter_audio) > 0:
                chapter_audio += AudioSegment.silent(duration=400)
            
            # Append this chunk's audio to our chapter audio
            chapter_audio += chunk_audio
            print(f'Processed chunk of length {len(chunk_audio)} ms')


        # End with 2 seconds of silence
        chapter_audio += AudioSegment.silent(duration=2000)

        # Export as M4A/AAC
        chapter_audio.export(
            m4a_path,
            format="ipod",  # This creates M4A/AAC format
            parameters=[
                "-codec:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-profile:a", "aac_low"  # AAC-LC profile
            ]
        )
        
        # Add M4A metadata tags
        audio = MP4(m4a_path)
        
        audio.tags['\xa9nam'] = chapter_title    # Title
        audio.tags['\xa9ART'] = author          # Artist
        audio.tags['\xa9alb'] = album           # Album
        audio.tags['trkn'] = [(int(chapter_num), 0)]  # Track number
        audio.tags['\xa9gen'] = 'Audiobook'     # Genre
        audio.tags['\xa9cmt'] = 'This book is read by an AI-generated voice.'  # Comment
        
        # Save the tags
        audio.save()
        print(f'Added M4A tags to "{m4a_path}"')
