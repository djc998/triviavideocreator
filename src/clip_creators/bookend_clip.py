from moviepy.editor import ColorClip, ImageClip, CompositeVideoClip, AudioFileClip
import json
import os
from .text_clip import create_text_clip

def create_bookend_clip(settings, project_dir, clip_type='intro', part_number=None, total_parts=None):
    """Create intro or end clip based on settings"""
    try:
        # Get clip settings path
        clip_path = settings[f'project_{clip_type}']
        if not clip_path:
            print(f"No {clip_type} clip path specified")
            return None
            
        # Get root directory (2 levels up from clip_creators)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Load clip settings
        with open(clip_path, 'r') as file:
            clip_settings = json.load(file)
            
        # Get video dimensions
        w = settings['video']['width']
        h = settings['video']['height']
        
        # Create background
        if clip_settings.get('background', {}).get('image'):
            # Convert relative path to absolute
            bg_path = os.path.join(root_dir, clip_settings['background']['image'].lstrip('/'))
            print(f"Using background image: {bg_path}")
            if not os.path.exists(bg_path):
                print(f"Warning: Background image not found at {bg_path}")
                # Fall back to color background
                hex_color = clip_settings['background']['color']
                rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                background = ColorClip(size=(w, h), color=rgb_color)
            else:
                background = ImageClip(bg_path)
                if background.size != (w, h):
                    background = background.resize((w, h))
        else:
            hex_color = clip_settings['background']['color']
            rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            background = ColorClip(size=(w, h), color=rgb_color)
        
        # Set clip duration
        duration = clip_settings['duration']
        background = background.set_duration(duration)
        
        # Create clips list with background
        clips = [background]
        
        # Add image clips if present
        if 'images' in clip_settings:
            for img_config in clip_settings['images']:
                try:
                    # Convert relative path to absolute
                    img_path = os.path.join(root_dir, img_config['file'].lstrip('/'))
                    print(f"Loading image: {img_path}")
                    
                    if not os.path.exists(img_path):
                        print(f"Warning: Image not found at {img_path}")
                        continue
                        
                    # Create image clip
                    img_clip = ImageClip(img_path)
                    
                    # Resize if width specified
                    if 'width' in img_config:
                        aspect_ratio = img_clip.size[1] / img_clip.size[0]
                        new_width = img_config['width']
                        new_height = int(new_width * aspect_ratio)
                        img_clip = img_clip.resize((new_width, new_height))
                    
                    # Calculate position
                    position = img_config['position']
                    padding = position.get('padding', 20)
                    
                    if position['x'] == 'right':
                        x = w - img_clip.size[0] - padding
                    elif position['x'] == 'left':
                        x = padding
                    else:  # center
                        x = (w - img_clip.size[0]) // 2
                        
                    if position['y'] == 'bottom':
                        y = h - img_clip.size[1] - padding
                    elif position['y'] == 'top':
                        y = padding
                    else:  # center
                        y = (h - img_clip.size[1]) // 2
                    
                    img_clip = img_clip.set_position((x, y))
                    
                    # Set duration and timing
                    if 'timing' in img_config:
                        timing = img_config['timing']
                        img_duration = timing.get('duration', duration)
                        img_clip = img_clip.set_duration(img_duration)
                        
                        # Set start time
                        if 'start' in timing:
                            img_clip = img_clip.set_start(timing['start'])
                            
                        # Add fade effects
                        if timing.get('fade', {}).get('enabled', False):
                            fade_duration = timing['fade'].get('duration', 0.5)
                            img_clip = img_clip.crossfadein(fade_duration)
                            img_clip = img_clip.crossfadeout(fade_duration)
                    
                    clips.append(img_clip)
                    print(f"Added image clip: {img_config['file']}")
                    
                except Exception as e:
                    print(f"Error adding image {img_config['file']}: {str(e)}")
                    continue
        
        # Add text clips
        for text_config in clip_settings['texts']:
            try:
                # Handle part number replacement
                content = text_config['content']
                if part_number is not None:
                    content = content.replace('{part_number}', str(part_number))
                if total_parts is not None:
                    content = content.replace('{total_parts}', str(total_parts))
                
                # Create text settings for this text element
                text_settings = {
                    'text': {
                        'font': text_config.get('font', settings['text']['font']),
                        'size': {'custom': text_config['size']},
                        'color': text_config['color'],
                        'shadow': settings['text']['shadow'],
                        'outline': settings['text']['outline'],
                        'custom': {
                            'position': text_config['position'],
                            'dimensions': text_config.get('dimensions', {'width': None, 'height': None})
                        },
                        'alignment': text_config.get('alignment', 'center'),
                        'wrap_width': text_config.get('wrap_width', settings['text']['wrap_width'])
                    },
                    'video': settings['video'],
                    'transitions': settings['transitions']
                }
                
                print(f"Creating text clip with position: {text_config['position']}")
                
                # Get timing settings
                timing = text_config.get('timing', {})
                text_duration = timing.get('duration', duration)
                
                # Create text clip
                text_clip = create_text_clip(
                    text=content,
                    duration=text_duration,
                    clip_type='custom',
                    settings=text_settings
                )
                
                # Handle timing
                if 'timing' in text_config:
                    # Set start time if specified
                    if 'start' in timing:
                        start_time = timing['start']
                        text_clip = text_clip.set_start(start_time)
                        print(f"Setting start time for text '{content}' to {start_time}")
                    
                    # Add fade effects if specified
                    if timing.get('fade', {}).get('enabled', True):
                        fade_duration = timing['fade'].get('duration', 0.5)
                        text_clip = text_clip.crossfadein(fade_duration)
                        if timing.get('duration'):
                            text_clip = text_clip.crossfadeout(fade_duration)
                
                clips.append(text_clip)
                print(f"Added text clip: {content}")
                
            except Exception as e:
                print(f"Error creating text clip: {str(e)}")
                continue
        
        # Create composite clip
        final_clip = CompositeVideoClip(clips, size=(w, h))
        final_clip = final_clip.set_duration(duration)
        
        # Add audio if specified
        if clip_settings.get('audio'):
            try:
                # Convert relative path to absolute
                audio_path = os.path.join(root_dir, clip_settings['audio']['file'].lstrip('/'))
                print(f"Loading audio from: {audio_path}")
                
                if not os.path.exists(audio_path):
                    print(f"Warning: Audio file not found at {audio_path}")
                else:
                    audio = AudioFileClip(audio_path)
                    
                    # Set volume if specified
                    if 'volume' in clip_settings['audio']:
                        volume = clip_settings['audio']['volume']
                        audio = audio.volumex(volume)
                        print(f"Set audio volume to: {volume}")
                    
                    # Set audio duration to match clip
                    audio = audio.subclip(0, duration)
                    
                    final_clip = final_clip.set_audio(audio)
                    print(f"Successfully added audio from: {audio_path}")
                    
            except Exception as e:
                print(f"Warning: Could not add audio to {clip_type} clip: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"Successfully created {clip_type} clip with duration: {duration} seconds")
        return final_clip
        
    except Exception as e:
        print(f"Error creating {clip_type} clip: {str(e)}")
        return None 