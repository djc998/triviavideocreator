from moviepy.editor import concatenate_videoclips, AudioFileClip, concatenate_audioclips
import numpy as np
from .settings import load_settings
from .clip_creators.qa_clip import create_qa_video
from .clip_creators.bookend_clip import create_bookend_clip
from .utils.text_utils import clean_text
import os

def generate_tiktok_videos(settings, questions_data, project_dir):
    """Generate TikTok format videos"""
    try:
        questions = questions_data['questions']
        questions_per_video = settings['tiktok_output']['questions_per_video']
        number_of_videos = settings['tiktok_output']['number_of_videos']
        filename_prefix = settings['tiktok_output']['filename_prefix']
        
        # Load audio if specified
        audio_clip = None
        if 'audio' in settings and settings['audio'].get('file'):
            try:
                audio_path = settings['audio']['file']
                print(f"\nLoading audio from: {audio_path}")
                
                if not os.path.exists(audio_path):
                    print(f"Error: Audio file not found at {audio_path}")
                else:
                    audio_clip = AudioFileClip(audio_path)
                    if 'volume' in settings['audio']:
                        volume = settings['audio']['volume']
                        audio_clip = audio_clip.volumex(volume)
                        print(f"Set audio volume to: {volume}")
                    print("Successfully loaded audio")
            except Exception as e:
                print(f"Error loading audio: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Generate each TikTok video
        for video_num in range(number_of_videos):
            print(f"\nGenerating TikTok video {video_num + 1} of {number_of_videos}")
            start_idx = video_num * questions_per_video
            end_idx = start_idx + questions_per_video
            video_questions = questions[start_idx:end_idx]
            
            clips = []
            
            # Create intro clip with part number
            if settings.get('project_intro'):
                print(f"\nCreating intro for part {video_num + 1}")
                intro_clip = create_bookend_clip(settings, project_dir, 'intro', 
                                               part_number=video_num + 1,
                                               total_parts=number_of_videos)
                if intro_clip:
                    clips.append(intro_clip)
            
            # Create question clips
            print(f"\nCreating {len(video_questions)} question clips...")
            for i, qa in enumerate(video_questions):
                print(f"Creating clip for question {i + 1}")
                clip = create_qa_video(
                    question=clean_text(qa['question']),
                    answer=clean_text(qa['answer']),
                    settings=settings,
                    audio_clip=None  # Don't pass audio to individual clips
                )
                clips.append(clip)
            
            # Create end clip with part number
            if settings.get('project_end'):
                print(f"\nCreating end clip for part {video_num + 1}")
                end_clip = create_bookend_clip(settings, project_dir, 'end',
                                             part_number=video_num + 1,
                                             total_parts=number_of_videos)
                if end_clip:
                    clips.append(end_clip)
            
            # Generate output filename
            output_filename = f"{filename_prefix}_{video_num + 1}.mp4"
            print(f"\nCreating video file: {output_filename}")
            
            # Concatenate clips
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Add audio if available
            if audio_clip:
                try:
                    # Loop audio if needed
                    if settings['audio'].get('loop', False):
                        total_duration = final_video.duration
                        num_loops = int(np.ceil(total_duration / audio_clip.duration))
                        print(f"Looping audio {num_loops} times to cover {total_duration} seconds")
                        audio_clips = [audio_clip] * num_loops
                        video_audio = concatenate_audioclips(audio_clips).subclip(0, total_duration)
                    else:
                        video_audio = audio_clip.subclip(0, min(audio_clip.duration, final_video.duration))
                    
                    final_video = final_video.set_audio(video_audio)
                    print("Successfully added audio to video")
                except Exception as e:
                    print(f"Error adding audio to video: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # Write final video
            final_video.write_videofile(
                output_filename,
                fps=settings['video']['fps'],
                codec=settings['video'].get('codec', 'libx264'),
                preset=settings['video'].get('preset', 'medium'),
                audio_codec='aac'  # Explicitly set audio codec
            )
            
    except Exception as e:
        print(f"Error in generate_tiktok_videos: {str(e)}")
        raise

def generate_standard_video(settings, questions_data, project_dir):
    """Generate a standard format video"""
    try:
        clips = []
        
        # Add intro if enabled
        if settings.get('project_intro'):
            print("\nAttempting to create intro clip...")
            intro_clip = create_bookend_clip(settings, project_dir, 'intro')
            if intro_clip:
                print("Adding intro clip to video")
                clips.append(intro_clip)
        
        print("\nCreating question clips...")
        # Handle preview mode
        if settings.get('preview_mode', {}).get('enabled', False):
            limit = settings['preview_mode']['questions_limit']
            print(f"Preview mode enabled: Processing first {limit} questions")
            questions = questions_data['questions'][:limit]
        else:
            questions = questions_data['questions']
        
        # Create question clips
        for i, qa in enumerate(questions, 1):
            print(f"Creating clip for question {i}")
            clip = create_qa_video(
                question=qa['question'],
                answer=qa['answer'],
                settings=settings
            )
            clips.append(clip)
        
        # Add end clip if enabled
        if settings.get('project_end'):
            print("Adding end clip to video")
            end_clip = create_bookend_clip(settings, project_dir, 'end')
            if end_clip:
                clips.append(end_clip)
        
        print(f"Final video will have {len(clips)} clips")
        
        # Combine all clips
        final_video = concatenate_videoclips(clips)
        
        # Add audio if specified
        if 'audio' in settings and settings['audio'].get('file'):
            try:
                audio_path = settings['audio']['file']
                print(f"\nProcessing audio...")
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
        print("\nWriting video file...")
        final_video.write_videofile(
            "output.mp4",
            fps=settings['video']['fps'],
            codec=settings['video'].get('codec', 'libx264'),
            preset=settings['video'].get('preset', 'medium'),
            audio_codec='aac'  # Explicitly set audio codec
        )
        
    except Exception as e:
        print(f"Error in generate_standard_video: {str(e)}")
        raise

def handle_preview_mode(settings, questions, intro_clip, end_clip):
    preview_type = settings['preview_mode'].get('type', 'questions')
    
    if preview_type == 'questions':
        limit = settings['preview_mode'].get('questions_limit', 2)
        questions = questions[:limit]
        print(f"Preview mode enabled: Processing first {limit} questions")
    elif preview_type == 'duration':
        questions = handle_duration_preview(settings, questions, intro_clip, end_clip)
    
    return questions

def handle_duration_preview(settings, questions, intro_clip, end_clip):
    duration_limit = settings['preview_mode'].get('duration_limit', 30)
    total_time = 0
    preview_questions = []
    
    # Add intro duration
    if intro_clip:
        total_time += intro_clip.duration
        print(f"Including intro duration: {intro_clip.duration} seconds")
    
    # Reserve time for end clip
    end_clip_duration = end_clip.duration if end_clip else 0
    available_time = duration_limit - end_clip_duration
    
    if end_clip:
        print(f"Reserving {end_clip_duration} seconds for end clip")
    
    # Add questions until time limit
    for q in questions:
        clip_duration = settings['timing']['question_duration'] + settings['timing']['answer_duration']
        
        if total_time + clip_duration <= available_time:
            preview_questions.append(q)
            total_time += clip_duration
            print(f"Added question, total duration now: {total_time} seconds")
        else:
            print(f"Duration limit ({available_time}s) would be exceeded, stopping")
            break
    
    total_with_end = total_time + end_clip_duration
    print(f"Preview mode enabled: Processing {len(preview_questions)} questions")
    print(f"Total duration will be: {total_with_end} seconds")
    
    return preview_questions

def add_audio_to_video(settings, final_video):
    try:
        # Load audio file
        audio = AudioFileClip(settings['audio']['file'])
        
        # Loop audio if needed
        if settings['audio'].get('loop', False):
            total_duration = final_video.duration
            num_loops = int(np.ceil(total_duration / audio.duration))
            audio_clips = [audio] * num_loops
            audio = concatenate_audioclips(audio_clips).subclip(0, total_duration)
        
        # Set volume if specified
        if 'volume' in settings['audio']:
            audio = audio.volumex(settings['audio']['volume'])
        
        # Combine audio with video
        final_video = final_video.set_audio(audio)
        
    except Exception as e:
        print(f"Warning: Could not add audio: {str(e)}")

def main():
    try:
        settings, questions_data, project_dir = load_settings()
        
        if settings.get('tiktok_output'):
            generate_tiktok_videos(settings, questions_data, project_dir)
        else:
            generate_standard_video(settings, questions_data, project_dir)
            
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    main() 