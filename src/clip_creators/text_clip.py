from moviepy.editor import TextClip, CompositeVideoClip
from ..utils.font_utils import get_font_path
from ..utils.position_utils import get_text_position
from ..utils.text_utils import wrap_text

def create_text_clip(text, duration, clip_type='question', settings=None):
    """Create a text clip with the specified settings"""
    try:
        # Get text settings
        if clip_type == 'custom' and 'custom' in settings['text']:
            font_size = settings['text']['size']['custom']
            position_settings = settings['text']['custom']['position']
        else:
            font_size = settings['text']['size'][clip_type]
            position_settings = settings['text'][clip_type]['position']
        
        print(f"Creating text clip with size: {font_size}")
        
        font_name = settings['text']['font']
        font = get_font_path(font_name, settings)
        
        # Get dimensions and text handling settings
        if clip_type == 'custom' and 'dimensions' in settings['text']['custom']:
            dimensions = settings['text']['custom']['dimensions']
        else:
            clip_settings = settings['text'][clip_type]
            dimensions = clip_settings.get('dimensions', {'width': None, 'height': None})
        
        # Create initial text clip without wrapping
        test_clip = TextClip(
            text,
            fontsize=font_size,
            color=settings['text']['color'],
            font=font,
            method='label',
            align=settings['text']['alignment'],
            bg_color='transparent'
        )
        
        # If width constraint exists and text is too wide
        if dimensions['width'] and test_clip.size[0] > dimensions['width']:
            # Calculate how many characters can fit per line
            chars_per_line = int((dimensions['width'] / test_clip.size[0]) * len(text))
            # Wrap text to multiple lines
            wrapped_text = wrap_text(text, chars_per_line)
        else:
            wrapped_text = text
        
        # Create final clip with wrapped text
        main_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            color=settings['text']['color'],
            font=font,
            method='label',
            align=settings['text']['alignment'],
            bg_color='transparent',
            stroke_color=settings['text'].get('outline', {}).get('color', '#000000') if settings['text'].get('outline', {}).get('enabled', False) else None,
            stroke_width=settings['text'].get('outline', {}).get('thickness', 2) if settings['text'].get('outline', {}).get('enabled', False) else 0
        )
        
        print(f"Created text clip with size {font_size}, dimensions: {main_clip.size}")
        
        # Create shadow if enabled
        if settings['text']['shadow']['enabled']:
            shadow_offset = settings['text']['shadow']['offset']
            shadow_color = settings['text']['shadow']['color']
            
            shadow = TextClip(
                wrapped_text,
                fontsize=font_size,
                color=shadow_color,
                font=font,
                method='label',
                align=settings['text']['alignment'],
                size=main_clip.size,
                bg_color='transparent'
            )
            
            # Create composite with shadow
            combined_clip = CompositeVideoClip(
                [
                    shadow.set_position((shadow_offset['x'], shadow_offset['y'])),
                    main_clip.set_position('center')
                ],
                size=main_clip.size
            )
        else:
            combined_clip = main_clip
        
        # Get clip dimensions for positioning
        clip_width = combined_clip.size[0]
        clip_height = combined_clip.size[1]
        
        # Calculate position for all clip types
        position = get_text_position(
            settings,
            clip_type,
            clip_width,
            clip_height,
            settings['video']['width'],
            settings['video']['height']
        )
        combined_clip = combined_clip.set_position(position)
        
        # Set duration and add crossfade
        combined_clip = combined_clip.set_duration(duration)
        combined_clip = combined_clip.crossfadein(settings['transitions']['duration'])
        
        return combined_clip
        
    except Exception as e:
        print(f"Error creating text clip: {str(e)}")
        raise 