from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips, ImageClip
from moviepy.config import change_settings
import json
import os
import textwrap
import numpy as np

# Configure MoviePy to use ImageMagick
# if os.name == 'nt':  # for Windows
#     change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1\\magick.exe"})

# Update the Mac path - this is typically the correct path when installed via Homebrew
change_settings({"IMAGEMAGICK_BINARY": r"/opt/homebrew/bin/convert"})

def load_settings():
    """Load settings from settings.json"""
    with open('settings.json', 'r') as file:
        return json.load(file)

def wrap_text(text, width):
    """Wrap text to specified width"""
    return '\n'.join(textwrap.wrap(text, width=width))

def create_text_clip(text, duration, clip_type='question', settings=None):
    wrapped_text = wrap_text(text, settings['text']['wrap_width'])
    
    # Get text settings
    font_size = settings['text']['size'][clip_type]
    font = settings['text']['font']
    text_color = settings['text']['color']
    shadow_enabled = settings['text']['shadow']['enabled']
    outline_enabled = settings['text'].get('outline', {}).get('enabled', False)
    
    # Create main text clip with transparent background
    main_clip = TextClip(wrapped_text, 
                        fontsize=font_size, 
                        color=text_color, 
                        font=font, 
                        method='label',
                        align=settings['text']['alignment'],
                        size=(settings['text']['max_width'], None),
                        bg_color='transparent',
                        stroke_color=settings['text'].get('outline', {}).get('color', '#000000') if outline_enabled else None,
                        stroke_width=settings['text'].get('outline', {}).get('thickness', 2) if outline_enabled else 0)
    
    if shadow_enabled:
        # Create shadow clip
        shadow_clip = TextClip(wrapped_text,
                             fontsize=font_size,
                             color=settings['text']['shadow']['color'],
                             font=font,
                             method='label',
                             align=settings['text']['alignment'],
                             size=(settings['text']['max_width'], None),
                             bg_color='transparent')
        
        # Offset shadow
        x_offset = settings['text']['shadow']['offset']['x']
        y_offset = settings['text']['shadow']['offset']['y']
        shadow_clip = shadow_clip.set_position(lambda t: (x_offset, y_offset))
        
        # Combine shadow and main text
        combined_clip = CompositeVideoClip([shadow_clip, main_clip])
    else:
        combined_clip = main_clip
    
    # Set position, duration and fade
    combined_clip = combined_clip.set_position('center')
    combined_clip = combined_clip.set_duration(duration)
    combined_clip = combined_clip.crossfadein(settings['transitions']['duration'])
    
    return combined_clip

def create_timer_clip(duration, start_time, settings):
    # Get timer settings
    shape_type = settings['timer'].get('shape', 'circle')
    if shape_type == 'circle':
        shape_settings = settings['timer']['circle']
    else:
        shape_settings = settings['timer']['square']
    
    size = shape_settings['size']
    shape_color = shape_settings['color'].lstrip('#')
    y_pos = shape_settings['position']['y']
    text_color = settings['timer']['text']['color']
    
    # Create shape background
    shape_surface = np.zeros((size, size, 3))
    
    if shape_type == 'circle':
        # Create circular mask
        center = size // 2
        y, x = np.ogrid[:size, :size]
        dist_from_center = np.sqrt((x - center)**2 + (y - center)**2)
        shape_mask = dist_from_center <= center
    else:
        # Create square mask (full surface)
        shape_mask = np.ones((size, size), dtype=bool)
    
    # Convert hex color to RGB and set shape color
    rgb_color = tuple(int(shape_color[i:i+2], 16) for i in (0, 2, 4))
    shape_surface[shape_mask] = rgb_color
    
    # Create shape clip
    shape_clip = ImageClip(shape_surface).set_duration(1)
    
    # Create timer text
    timer_text = str(int(duration - start_time))
    text_clip = TextClip(
        timer_text, 
        fontsize=settings['text']['size']['timer'], 
        color=text_color,
        font=settings['text']['font'],
        method='label',
        align='center',
        bg_color='transparent'
    )
    
    # Center text on shape
    text_clip = text_clip.set_position(('center', 'center'))
    
    # Combine shape and text
    combined_clip = CompositeVideoClip(
        [shape_clip, text_clip],
        size=(size, size)
    )
    
    # Position the combined timer in the video
    combined_clip = combined_clip.set_position(('center', y_pos))
    
    # Add timer sound if enabled
    if settings['timer'].get('sound', {}).get('enabled', False):
        sound_file = settings['timer']['sound'].get('file')
        if sound_file and os.path.exists(sound_file):
            try:
                tick_sound = AudioFileClip(sound_file)
                if settings['timer']['sound'].get('volume'):
                    tick_sound = tick_sound.volumex(settings['timer']['sound']['volume'])
                combined_clip = combined_clip.set_audio(tick_sound)
            except Exception as e:
                print(f"Warning: Could not load timer sound: {str(e)}")
    
    # Set duration BEFORE applying crossfade
    combined_clip = combined_clip.set_duration(1)
    
    # Add fade in for first number
    if start_time == 0:
        combined_clip = combined_clip.crossfadein(settings['transitions']['duration'])
    
    return combined_clip

def create_qa_video(question, answer, settings, audio_clip=None):
    # Get video dimensions and durations
    w = settings['video']['width']
    h = settings['video']['height']
    q_duration = settings['timing']['question_duration']
    a_duration = settings['timing']['answer_duration']
    total_duration = q_duration + a_duration
    
    try:
        # Create background based on settings
        if 'background_image' in settings and os.path.exists(settings['background_image']):
            # Use background image if specified and exists
            background = ImageClip(settings['background_image'])
            # Resize to match video dimensions if needed
            if background.size != (w, h):
                background = background.resize((w, h))
            background = background.set_duration(total_duration)
        else:
            # Fall back to color background if no image or image not found
            hex_color = settings['background']['color']
            rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            background = ColorClip(size=(w, h), color=rgb_color).set_duration(total_duration)
        
        # Create question and answer clips
        question_clip = create_text_clip(question, q_duration, 'question', settings)
        answer_clip = create_text_clip(answer, a_duration, 'answer', settings).set_start(q_duration)
        
        # Create base composite without timer
        base_composite = CompositeVideoClip([background, question_clip, answer_clip], size=(w, h))
        
        # Create timer clips for question duration only
        timer_clips = []
        for i in range(q_duration):
            timer = create_timer_clip(q_duration, i, settings)
            timer_clips.append(timer.set_start(i))
        
        # Create final composite with timer on top
        final_clip = CompositeVideoClip([base_composite] + timer_clips, size=(w, h))
        
        # Add audio if provided
        if audio_clip:
            final_clip = final_clip.set_audio(audio_clip.subclip(0, total_duration))
            
        final_clip = final_clip.set_duration(total_duration)
        return final_clip
    
    except Exception as e:
        print(f"Error in create_qa_video: {str(e)}")
        raise

def clean_text(text):
    """Clean text by replacing escaped quotes and other potential issues"""
    return text.replace('\\"', '"')

def main():
    try:
        # Load settings
        settings = load_settings()
        
        # Read questions from JSON file
        with open('questions.json', 'r') as file:
            data = json.load(file)
        
        # If preview mode is enabled, limit the number of questions
        questions = data['questions']
        if settings.get('preview_mode', {}).get('enabled', False):
            limit = settings['preview_mode'].get('questions_limit', 2)
            questions = questions[:limit]
            print(f"Preview mode enabled: Processing first {limit} questions only")
        
        # Create video clips first to calculate total duration
        clips = []
        for qa in questions:
            clip = create_qa_video(
                question=clean_text(qa['question']),
                answer=clean_text(qa['answer']),
                settings=settings,
                audio_clip=None  # No audio yet
            )
            clips.append(clip)
        
        # Concatenate video clips
        final_video = concatenate_videoclips(clips)
        total_duration = final_video.duration
        
        # Load and prepare audio if specified
        audio_clip = None
        if 'audio' in settings and settings['audio'].get('file'):
            audio_path = settings['audio']['file']
            if os.path.exists(audio_path):
                try:
                    # Load the original audio
                    original_audio = AudioFileClip(audio_path)
                    
                    if settings['audio'].get('loop', True):
                        # Calculate how many complete loops we need
                        loops_needed = int(total_duration / original_audio.duration) + 1
                        # Create concatenated audio clips
                        audio_clips = [original_audio] * loops_needed
                        audio_clip = concatenate_audioclips(audio_clips)
                        # Trim to exact video duration
                        audio_clip = audio_clip.subclip(0, total_duration)
                    else:
                        audio_clip = original_audio
                    
                    # Apply volume adjustment if specified
                    if settings['audio'].get('volume'):
                        audio_clip = audio_clip.volumex(settings['audio']['volume'])
                    
                    # Set the audio for the final video
                    final_video = final_video.set_audio(audio_clip)
                    
                except Exception as e:
                    print(f"Warning: Could not load audio file: {str(e)}")
                    audio_clip = None
        
        # Write the final video
        final_video.write_videofile(
            "output.mp4",
            fps=settings['video']['fps'],
            codec=settings['video']['codec'],
            audio=True if audio_clip else False,
            threads=4,
            preset=settings['video']['preset']
        )
        
        # Clean up
        if audio_clip:
            audio_clip.close()
        for clip in clips:
            clip.close()
        final_video.close()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 