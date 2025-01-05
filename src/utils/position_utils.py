def get_text_position(settings, clip_type, clip_width, clip_height, video_width, video_height):
    """Calculate text position based on settings"""
    try:
        # Get position settings for this clip type
        if clip_type == 'custom':
            position = settings['text']['custom']['position']
        else:
            position = settings['text'][clip_type]['position']
            
        padding = position.get('padding', 20)
        
        # Calculate x position
        x_setting = position.get('x', 'center')
        if x_setting == 'center':
            x = (video_width - clip_width) // 2
        elif x_setting == 'left':
            x = padding
        elif x_setting == 'right':
            x = video_width - clip_width - padding
        else:
            # Try to use as numeric value
            try:
                x = int(x_setting)
            except (ValueError, TypeError):
                print(f"Invalid x position '{x_setting}', using center")
                x = (video_width - clip_width) // 2
        
        # Calculate y position
        y_setting = position.get('y', 'center')
        if y_setting == 'center':
            y = (video_height - clip_height) // 2
        elif y_setting == 'top':
            y = padding
        elif y_setting == 'bottom':
            y = video_height - clip_height - padding
        else:
            # Try to use as numeric value
            try:
                y = int(y_setting)
            except (ValueError, TypeError):
                print(f"Invalid y position '{y_setting}', using center")
                y = (video_height - clip_height) // 2
        
        print(f"Calculated position for {clip_type}: ({x}, {y})")
        return (x, y)
        
    except Exception as e:
        print(f"Error calculating position: {str(e)}")
        # Return center position as fallback
        x = (video_width - clip_width) // 2
        y = (video_height - clip_height) // 2
        print(f"Using fallback center position: ({x}, {y})")
        return (x, y) 