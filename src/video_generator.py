def main():
    try:
        settings = load_settings()
        
        # Create video clips
        clips = []
        
        # ... (other video creation code)
        
        # Combine all clips
        final_video = concatenate_videoclips(clips)
        
        # Add audio if specified
        if 'audio' in settings and settings['audio'].get('file'):
            try:
                audio_path = settings['audio']['file']  # Path should already be absolute from settings.py
                print(f"Loading audio from: {audio_path}")
                
                if not os.path.exists(audio_path):
                    print(f"Error: Audio file not found at {audio_path}")
                else:
                    audio = AudioFileClip(audio_path)
                    
                    # Loop audio if needed
                    if settings['audio'].get('loop', False):
                        total_duration = final_video.duration
                        num_loops = int(np.ceil(total_duration / audio.duration))
                        print(f"Looping audio {num_loops} times to cover {total_duration} seconds")
                        audio_clips = [audio] * num_loops
                        audio = concatenate_audioclips(audio_clips).subclip(0, total_duration)
                    
                    # Set volume if specified
                    if 'volume' in settings['audio']:
                        volume = settings['audio']['volume']
                        audio = audio.volumex(volume)
                        print(f"Set audio volume to: {volume}")
                    
                    # Combine audio with video
                    final_video = final_video.set_audio(audio)
                    print("Successfully added audio to video")
                    
            except Exception as e:
                print(f"Error adding audio: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Write final video
        print("Writing video file...")
        final_video.write_videofile(
            "output.mp4",
            fps=settings['video']['fps'],
            codec=settings['video'].get('codec', 'libx264'),
            preset=settings['video'].get('preset', 'medium')
        )
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise 