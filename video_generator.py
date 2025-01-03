from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips, ImageClip
from moviepy.config import change_settings
import json
import os
import textwrap
import numpy as np
from pathlib import Path

# Configure MoviePy to use ImageMagick
# if os.name == 'nt':  # for Windows
#     change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1\\magick.exe"})

# Update the Mac path - this is typically the correct path when installed via Homebrew
change_settings({"IMAGEMAGICK_BINARY": r"/opt/homebrew/bin/convert"})

def load_settings():
    """Load settings and project settings"""
    # Get the root directory of the application
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Root directory: {root_dir}")
    
    # Load main settings file
    with open('settings.json', 'r') as file:
        main_settings = json.load(file)
    
    # Get project paths
    project_settings_path = main_settings['project']
    project_dir = os.path.dirname(project_settings_path)
    print(f"Project directory: {project_dir}")
    
    # Store intro and end paths in project settings
    project_intro_path = main_settings.get('project_intro', '')
    project_end_path = main_settings.get('project_end', '')
    
    # Load project settings
    with open(project_settings_path, 'r') as file:
        project_settings = json.load(file)
    
    # Add bookend paths to project settings
    project_settings['project_intro'] = project_intro_path
    project_settings['project_end'] = project_end_path
    
    # Add font directories from main settings to project settings
    project_settings['font_directories'] = main_settings.get('font_directories', [
        '/Library/Fonts/',  # macOS
        '/System/Library/Fonts/',  # macOS System
        'C:\\Windows\\Fonts\\',  # Windows
        '/usr/share/fonts/',  # Linux
        os.path.join(os.path.dirname(__file__), 'fonts/')  # Local fonts directory
    ])
    
    # Load questions
    questions_path = os.path.join(project_dir, project_settings['questions_file'])
    print(f"Questions path: {questions_path}")
    
    with open(questions_path, 'r') as file:
        questions_data = json.load(file)
    
    # Debug print settings before path updates
    print(f"Background image before: {project_settings.get('background_image', 'Not set')}")
    
    # Update paths to be relative to root directory for media files
    if 'background_image' in project_settings:
        if project_settings['background_image']:  # Only update if not empty
            project_settings['background_image'] = os.path.join(root_dir, project_settings['background_image'].lstrip('/'))
            print(f"Background image after: {project_settings['background_image']}")
        else:
            project_settings['background_image'] = ''  # Ensure it's an empty string
            print("Background image is empty, using color background")
    
    if 'audio' in project_settings and 'file' in project_settings['audio']:
        project_settings['audio']['file'] = os.path.join(root_dir, project_settings['audio']['file'].lstrip('/'))
        print(f"Audio file path: {project_settings['audio']['file']}")
    
    if 'timer' in project_settings and 'sound' in project_settings['timer']:
        project_settings['timer']['sound']['file'] = os.path.join(root_dir, project_settings['timer']['sound']['file'].lstrip('/'))
        print(f"Timer sound path: {project_settings['timer']['sound']['file']}")
    
    return project_settings, questions_data, project_dir

def wrap_text(text, width):
    """Wrap text to specified width"""
    return '\n'.join(textwrap.wrap(text, width=width))

def get_text_position(settings, clip_type, clip_width, clip_height, video_width, video_height):
    """Calculate text position based on settings"""
    position = settings['text'][clip_type]['position']
    x_setting = position.get('x', 'center')
    y_setting = position.get('y', 'center')
    padding = position.get('padding', 20)
    
    # Calculate x position
    if isinstance(x_setting, (int, float)) or str(x_setting).isdigit():
        x_pos = int(x_setting)  # Convert to int if it's a string number
    elif x_setting == "center":
        x_pos = 'center'
    elif x_setting == "left":
        x_pos = padding
    elif x_setting == "right":
        x_pos = video_width - clip_width - padding
    else:
        x_pos = 'center'
    
    # Calculate y position
    if isinstance(y_setting, (int, float)) or str(y_setting).isdigit():
        y_pos = int(y_setting)  # Convert to int if it's a string number
    elif y_setting == "center":
        y_pos = 'center'
    elif y_setting == "top":
        y_pos = padding
    elif y_setting == "bottom":
        y_pos = video_height - clip_height - padding
    else:
        y_pos = 'center'
    
    return (x_pos, y_pos)

def get_font_path(font_name, settings):
    """Get the full path for a font name"""
    # Split font name and index if provided (e.g., "Phosphate:1" -> "Phosphate", "1")
    font_parts = font_name.split(':')
    base_font_name = font_parts[0]
    
    if len(font_parts) > 1:
        # For TTC fonts with index, use the font family name with the style
        if base_font_name == "Phosphate":
            return "Phosphate-Solid" if font_parts[1] == "1" else "Phosphate"
    
    return base_font_name

def create_text_clip(text, duration, clip_type='question', settings=None):
    wrapped_text = wrap_text(text, settings['text']['wrap_width'])
    
    # Get text settings
    font_size = settings['text']['size'][clip_type]
    font_name = settings['text']['font']
    font = get_font_path(font_name, settings)
    print(f"Creating text clip with font: {font}")
    
    text_color = settings['text']['color']
    shadow_enabled = settings['text']['shadow']['enabled']
    outline_enabled = settings['text'].get('outline', {}).get('enabled', False)
    
    # Get dimensions - handle both old and new format
    if clip_type == 'custom' and 'dimensions' in settings['text']['custom']:
        dimensions = settings['text']['custom']['dimensions']
    else:
        # For question/answer clips, check for both new and old format
        clip_settings = settings['text'][clip_type]
        if 'dimensions' in clip_settings:
            dimensions = clip_settings['dimensions']
        else:
            # Fallback to old format or default
            dimensions = {
                'width': clip_settings.get('width', 1000),
                'height': None
            }
    
    max_width = dimensions.get('width', None)
    max_height = dimensions.get('height', None)
    
    # Create size tuple based on dimensions
    size = (max_width, max_height) if max_width or max_height else None
    
    # Create main text clip with transparent background
    try:
        main_clip = TextClip(
            wrapped_text, 
            fontsize=font_size, 
            color=text_color, 
            font=font,
            method='label',
            align=settings['text']['alignment'],
            size=size,  # Now using both width and height if specified
            bg_color='transparent',
            stroke_color=settings['text'].get('outline', {}).get('color', '#000000') if outline_enabled else None,
            stroke_width=settings['text'].get('outline', {}).get('thickness', 2) if outline_enabled else 0
        )
        print(f"Successfully created text clip with font: {font}")
        if size:
            print(f"Text clip dimensions: {main_clip.size}")
    except Exception as e:
        print(f"Error creating text clip with font {font}: {str(e)}")
        raise
    
    if shadow_enabled:
        # Create shadow clip
        shadow_clip = TextClip(wrapped_text,
                             fontsize=font_size,
                             color=settings['text']['shadow']['color'],
                             font=font,
                             method='label',
                             align=settings['text']['alignment'],
                             size=(max_width, None),
                             bg_color='transparent')
        
        # Offset shadow
        x_offset = settings['text']['shadow']['offset']['x']
        y_offset = settings['text']['shadow']['offset']['y']
        shadow_clip = shadow_clip.set_position(lambda t: (x_offset, y_offset))
        
        # Combine shadow and main text
        combined_clip = CompositeVideoClip([shadow_clip, main_clip])
    else:
        combined_clip = main_clip
    
    # Get the actual height of the clip
    clip_height = combined_clip.size[1]
    
    # Calculate position
    position = get_text_position(
        settings, 
        clip_type, 
        max_width, 
        clip_height,  # Pass the actual clip height
        settings['video']['width'], 
        settings['video']['height']
    )
    
    # Set position, duration and fade
    combined_clip = combined_clip.set_position(position)
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
    position = shape_settings['position']
    text_color = settings['timer']['text']['color']
    
    # Get video dimensions for positioning
    video_width = settings['video']['width']
    
    # Create shape background with alpha channel (RGBA)
    shape_surface = np.zeros((size, size, 4))
    
    if shape_type == 'circle':
        # Create circular mask
        center = size // 2
        y, x = np.ogrid[:size, :size]
        dist_from_center = np.sqrt((x - center)**2 + (y - center)**2)
        shape_mask = dist_from_center <= center
        
        # Set alpha to 0 (transparent) everywhere except the circle
        shape_surface[..., 3] = 0
        shape_surface[shape_mask, 3] = 255
    else:
        # Create square mask (full surface)
        shape_mask = np.ones((size, size), dtype=bool)
        shape_surface[..., 3] = 255
    
    # Convert hex color to RGB and set shape color
    rgb_color = tuple(int(shape_color[i:i+2], 16) for i in (0, 2, 4))
    shape_surface[shape_mask, 0:3] = rgb_color
    
    # Create shape clip with transparency
    shape_clip = ImageClip(shape_surface, ismask=False, transparent=True).set_duration(1)
    
    # Create timer text with proper font
    timer_text = str(int(duration - start_time))
    font_name = settings['text']['font']
    font = get_font_path(font_name, settings)  # Pass settings to get_font_path
    
    text_clip = TextClip(
        timer_text, 
        fontsize=settings['text']['size']['timer'], 
        color=text_color,
        font=font,  # Use resolved font path
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
    
    # Calculate position
    x_setting = position.get('x', 'center')
    if x_setting == "center":
        pos = ('center', position['y'])
    else:
        padding = position.get('padding', 20)
        if isinstance(x_setting, (int, float)):
            x_pos = x_setting
        elif x_setting == "left":
            x_pos = padding
        elif x_setting == "right":
            x_pos = video_width - size - padding
        else:
            x_pos = "center"
        pos = (x_pos, position['y'])
    
    # Position the combined timer in the video
    combined_clip = combined_clip.set_position(pos)
    
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
        if ('background_image' in settings and 
            settings['background_image'] and 
            os.path.exists(settings['background_image'])):
            print(f"Using background image: {settings['background_image']}")
            background = ImageClip(settings['background_image'])
            if background.size != (w, h):
                background = background.resize((w, h))
            background = background.set_duration(total_duration)
        else:
            print("Using color background")
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

def create_bookend_clip(settings, project_dir, clip_type='intro'):
    """Create intro or end clip based on settings"""
    try:
        # Load clip settings
        filename = f'project_{clip_type}.json'
        clip_path = os.path.join(project_dir, filename)
        print(f"Looking for {clip_type} settings at: {clip_path}")
        
        if not os.path.exists(clip_path):
            print(f"No {filename} found")
            return None
            
        with open(clip_path, 'r') as file:
            clip_settings = json.load(file)
            
        if not clip_settings.get('enabled', False):
            print(f"{clip_type.capitalize()} clip is disabled in settings")
            return None
            
        print(f"Creating {clip_type} clip...")
        # Get video dimensions
        w = settings['video']['width']
        h = settings['video']['height']
        duration = clip_settings.get('duration', 5)
        
        # Create background
        if 'background' in clip_settings and clip_settings['background'].get('image'):
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 clip_settings['background']['image'].lstrip('/'))
            if os.path.exists(bg_path):
                background = ImageClip(bg_path)
                if background.size != (w, h):
                    background = background.resize((w, h))
            else:
                hex_color = clip_settings['background']['color']
                rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                background = ColorClip(size=(w, h), color=rgb_color)
        else:
            hex_color = clip_settings['background']['color']
            rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            background = ColorClip(size=(w, h), color=rgb_color)
        
        background = background.set_duration(duration)
        
        # Create base clips list with background
        clips = [background]
        
        # Add image clips if present
        if 'images' in clip_settings:
            for image_config in clip_settings['images']:
                try:
                    # Get image path relative to project directory first, then try root directory
                    root_dir = os.path.dirname(os.path.abspath(__file__))
                    image_path = image_config['file']
                    
                    # First try project directory
                    project_image_path = os.path.join(project_dir, image_path)
                    if os.path.exists(project_image_path):
                        full_image_path = project_image_path
                    else:
                        # Fallback to root directory
                        if image_path.startswith('/'):
                            image_path = image_path[1:]
                        full_image_path = os.path.join(root_dir, image_path)
                    
                    print(f"\nProcessing {clip_type} image:")
                    print(f"Original path: {image_config['file']}")
                    print(f"Project directory path: {project_image_path}")
                    print(f"Root directory path: {full_image_path}")
                    
                    if not os.path.exists(full_image_path):
                        print(f"Warning: Image not found at: {full_image_path}")
                        continue
                    
                    print(f"Loading image from: {full_image_path}")
                    img_clip = ImageClip(full_image_path)
                    print(f"Original image size: {img_clip.size}")
                    
                    # Process image (resize, timing, position, fade)
                    img_clip = process_media_clip(img_clip, image_config, w, h, duration, settings)
                    clips.append(img_clip)
                    
                except Exception as e:
                    print(f"Error processing image: {str(e)}")
                    continue
        
        # Add text clips
        for text_config in clip_settings['texts']:
            # Convert from old format to new if necessary
            if 'width' in text_config:
                dimensions = {
                    'width': text_config.pop('width'),
                    'height': None
                }
            else:
                dimensions = text_config.get('dimensions', {'width': 1000, 'height': None})
            
            text_clip = create_text_clip(
                text=text_config['content'],
                duration=text_config.get('timing', {}).get('duration', duration),
                clip_type='custom',
                settings={
                    'text': {
                        'font': text_config['font'],
                        'size': {'custom': text_config['size']},
                        'color': text_config['color'],
                        'shadow': text_config.get('shadow', {'enabled': False}),
                        'outline': text_config.get('outline', {'enabled': False}),
                        'custom': {
                            'position': text_config['position'],
                            'dimensions': dimensions
                        },
                        'alignment': 'center',
                        'wrap_width': settings['text']['wrap_width']
                    },
                    'video': settings['video'],
                    'transitions': settings['transitions']
                }
            )
            
            # Process text clip (timing, fade)
            text_clip = process_media_clip(text_clip, text_config, w, h, duration, settings)
            clips.append(text_clip)
        
        # Combine all clips
        final_clip = CompositeVideoClip(clips, size=(w, h))
        final_clip = final_clip.set_duration(duration)
        
        print(f"Successfully created {clip_type} clip with duration: {duration} seconds")
        return final_clip
        
    except Exception as e:
        print(f"Error creating {clip_type} clip: {str(e)}")
        return None

def process_media_clip(clip, config, width, height, default_duration, settings):
    """Process a media clip with timing, position, and fade settings"""
    # Resize image if width specified (for image clips only)
    if isinstance(clip, ImageClip) and config.get('width'):
        aspect_ratio = clip.size[1] / clip.size[0]
        new_width = config['width']
        new_height = int(new_width * aspect_ratio)
        clip = clip.resize((new_width, new_height))
        print(f"Resized clip to: {clip.size}")
    
    # Get timing settings
    timing = config.get('timing', {
        'start': 0,
        'duration': default_duration,
        'fade': {'enabled': True, 'duration': settings['transitions']['duration']}
    })
    
    # Set duration
    clip = clip.set_duration(timing['duration'])
    
    # Apply position if specified
    if 'position' in config:
        position = config['position']
        x_setting = position.get('x', 'center')
        y_setting = position.get('y', 'center')
        padding = position.get('padding', 20)
        
        print(f"Positioning clip with settings: x={x_setting}, y={y_setting}, padding={padding}")
        print(f"Clip size: {clip.size}")
        
        # Calculate x position
        if x_setting == "center":
            x_pos = 'center'
        elif x_setting == "left":
            x_pos = padding
        elif x_setting == "right":
            x_pos = width - clip.size[0] - padding
        else:
            x_pos = int(x_setting)
        
        # Calculate y position
        if y_setting == "center":
            y_pos = 'center'
        elif y_setting == "top":
            y_pos = padding
        elif y_setting == "bottom":
            y_pos = height - clip.size[1] - padding
        else:
            y_pos = int(y_setting)
            
        print(f"Final position: ({x_pos}, {y_pos})")
        clip = clip.set_position((x_pos, y_pos))
    
    # Apply fade if enabled
    if timing['fade'].get('enabled', True):
        fade_duration = timing['fade'].get('duration', settings['transitions']['duration'])
        clip = clip.crossfadein(fade_duration)
    
    # Set start time
    clip = clip.set_start(timing['start'])
    
    return clip

def main():
    try:
        # Load settings and questions
        settings, questions_data, project_dir = load_settings()
        
        # Create intro clip if path is specified
        intro_clip = None
        if settings.get('project_intro'):
            print("\nAttempting to create intro clip...")
            intro_clip = create_bookend_clip(settings, project_dir, 'intro')
        else:
            print("\nNo intro clip path specified, skipping...")
        
        # Create end clip if path is specified
        end_clip = None
        if settings.get('project_end'):
            print("\nAttempting to create end clip...")
            end_clip = create_bookend_clip(settings, project_dir, 'end')
        else:
            print("\nNo end clip path specified, skipping...")
        
        # Get questions
        questions = questions_data['questions']
        
        # Handle preview mode
        if settings.get('preview_mode', {}).get('enabled', False):
            preview_type = settings['preview_mode'].get('type', 'questions')
            
            if preview_type == 'questions':
                limit = settings['preview_mode'].get('questions_limit', 2)
                questions = questions[:limit]
                print(f"Preview mode enabled: Processing first {limit} questions")
            elif preview_type == 'duration':
                duration_limit = settings['preview_mode'].get('duration_limit', 30)
                total_time = 0
                preview_questions = []
                
                # Add intro duration if present
                if intro_clip:
                    total_time += intro_clip.duration
                    print(f"Including intro duration: {intro_clip.duration} seconds")
                
                # Reserve time for end clip if present
                end_clip_duration = end_clip.duration if end_clip else 0
                available_time = duration_limit - end_clip_duration
                
                if end_clip:
                    print(f"Reserving {end_clip_duration} seconds for end clip")
                
                # Add questions until we hit the available time limit
                for q in questions:
                    clip_duration = settings['timing']['question_duration'] + settings['timing']['answer_duration']
                    
                    if total_time + clip_duration <= available_time:
                        preview_questions.append(q)
                        total_time += clip_duration
                        print(f"Added question, total duration now: {total_time} seconds")
                    else:
                        print(f"Duration limit ({available_time}s) would be exceeded, stopping")
                        break
                
                questions = preview_questions
                total_with_end = total_time + end_clip_duration
                print(f"Preview mode enabled: Processing {len(questions)} questions")
                print(f"Total duration will be: {total_with_end} seconds")
        
        # Create video clips
        clips = []
        
        # Add intro if present
        if intro_clip:
            print("Adding intro clip to video")
            clips.append(intro_clip)
        
        # Add question clips
        print("\nCreating question clips...")
        for i, qa in enumerate(questions):
            print(f"Creating clip for question {i+1}")
            clip = create_qa_video(
                question=clean_text(qa['question']),
                answer=clean_text(qa['answer']),
                settings=settings,
                audio_clip=None
            )
            clips.append(clip)
        
        # Add end clip if present
        if end_clip:
            print("Adding end clip to video")
            clips.append(end_clip)
            
        print(f"Final video will have {len(clips)} clips")
        
        # Concatenate video clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add audio if specified
        if 'audio' in settings and settings['audio'].get('file'):
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
        
        # Write final video
        final_video.write_videofile(
            "output.mp4",
            fps=settings['video']['fps'],
            codec=settings['video'].get('codec', 'libx264'),
            preset=settings['video'].get('preset', 'medium')
        )
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 