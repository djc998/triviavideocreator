from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
import numpy as np
from ..utils.font_utils import get_font_path

def create_timer_clip(duration, start_time, settings):
    """Create a timer clip with the specified settings"""
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
    
    # Convert hex color to RGB and set the color for the shape
    r = int(shape_color[:2], 16)
    g = int(shape_color[2:4], 16)
    b = int(shape_color[4:], 16)
    shape_surface[shape_mask] = [r, g, b, 255]
    
    # Create shape clip
    shape_clip = ImageClip(shape_surface.astype('uint8'))
    
    # Create text for timer
    remaining_time = duration - start_time
    timer_text = str(remaining_time)
    
    # Create text clip
    text_clip = TextClip(
        timer_text,
        fontsize=settings['text']['size']['timer'],
        color=text_color,
        font=get_font_path(settings['text']['font'], settings),
        method='label'
    )
    
    # Center text in shape
    text_pos = ((size - text_clip.size[0]) // 2, (size - text_clip.size[1]) // 2)
    
    # Combine shape and text
    timer_clip = CompositeVideoClip(
        [shape_clip, text_clip.set_position(text_pos)],
        size=(size, size)
    )
    
    # Calculate timer position
    x_setting = position.get('x', 'right')
    padding = position.get('padding', 20)
    
    if x_setting == 'right':
        x_pos = video_width - size - padding
    elif x_setting == 'left':
        x_pos = padding
    elif x_setting == 'center':
        x_pos = (video_width - size) // 2
    else:
        x_pos = int(x_setting)
    
    y_pos = position.get('y', 10)
    if isinstance(y_pos, str):
        if y_pos == 'top':
            y_pos = padding
        elif y_pos == 'center':
            y_pos = (settings['video']['height'] - size) // 2
        elif y_pos == 'bottom':
            y_pos = settings['video']['height'] - size - padding
    
    timer_clip = timer_clip.set_position((x_pos, y_pos))
    
    # Add timer sound if enabled
    if settings['timer'].get('sound', {}).get('enabled', False):
        try:
            sound_file = settings['timer']['sound']['file']
            volume = settings['timer']['sound'].get('volume', 1.0)
            audio = AudioFileClip(sound_file).volumex(volume)
            timer_clip = timer_clip.set_audio(audio)
        except Exception as e:
            print(f"Warning: Could not add timer sound: {str(e)}")
    
    # Set duration for this frame of the timer
    timer_clip = timer_clip.set_duration(1)  # Each number shows for 1 second
    
    return timer_clip 