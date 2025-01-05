from moviepy.editor import ColorClip, ImageClip, CompositeVideoClip
from .text_clip import create_text_clip
from .timer_clip import create_timer_clip

def create_qa_video(question, answer, settings, audio_clip=None):
    """Create a video clip for a question and answer"""
    try:
        # Get video dimensions
        w = settings['video']['width']
        h = settings['video']['height']
        
        # Get durations
        q_duration = settings['timing']['question_duration']
        a_duration = settings['timing']['answer_duration']
        total_duration = q_duration + a_duration
        
        # Create background
        if settings.get('background', {}).get('image'):
            print(f"Using background image: {settings['background']['image']}")
            background = ImageClip(settings['background']['image'])
            if background.size != (w, h):
                background = background.resize((w, h))
        else:
            hex_color = settings['background']['color']
            rgb_color = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            background = ColorClip(size=(w, h), color=rgb_color)
        
        background = background.set_duration(total_duration)
        
        # Create clips list with background
        clips = [background]
        
        # Create question text
        question_clip = create_text_clip(question, q_duration, 'question', settings)
        question_clip = question_clip.set_start(0)
        clips.append(question_clip)
        
        # Create answer text
        answer_clip = create_text_clip(answer, a_duration, 'answer', settings)
        answer_clip = answer_clip.set_start(q_duration)
        clips.append(answer_clip)
        
        # Create timer clips for question duration only
        for i in range(q_duration):
            timer = create_timer_clip(q_duration, i, settings)
            timer = timer.set_start(i)
            clips.append(timer)
        
        # Add overlays if present
        if 'overlays' in settings['text']:
            for overlay in settings['text']['overlays']:
                # Only process enabled overlays
                if overlay.get('enabled', True):  # Default to True for backward compatibility
                    try:
                        # Create overlay text clip
                        overlay_duration = total_duration if overlay['timing']['duration'] == 'full' else overlay['timing']['duration']
                        overlay_clip = create_text_clip(
                            text=overlay['content'],
                            duration=overlay_duration,
                            clip_type='custom',
                            settings={
                                'text': {
                                    'font': overlay['font'],
                                    'size': {'custom': overlay['size']},
                                    'color': overlay['color'],
                                    'shadow': overlay.get('shadow', {'enabled': False}),
                                    'outline': overlay.get('outline', {'enabled': False}),
                                    'custom': {
                                        'position': overlay['position'],
                                        'dimensions': overlay.get('dimensions', {'width': 400, 'height': None})
                                    },
                                    'alignment': 'center',
                                    'wrap_width': settings['text']['wrap_width']
                                },
                                'video': settings['video'],
                                'transitions': settings['transitions']
                            }
                        )
                        
                        # Apply timing
                        overlay_clip = overlay_clip.set_start(overlay['timing']['start'])
                        
                        # Apply fade if enabled
                        if overlay['timing'].get('fade', {}).get('enabled', True):
                            fade_duration = overlay['timing']['fade'].get('duration', settings['transitions']['duration'])
                            overlay_clip = overlay_clip.crossfadein(fade_duration)
                        
                        clips.append(overlay_clip)
                        print(f"Added overlay text: {overlay['content']}")
                        
                    except Exception as e:
                        print(f"Error creating overlay text: {str(e)}")
                        continue
        
        # Combine all clips
        final_clip = CompositeVideoClip(clips, size=(w, h))
        final_clip = final_clip.set_duration(total_duration)
        
        # Add audio if provided
        if audio_clip:
            final_clip = final_clip.set_audio(audio_clip.subclip(0, total_duration))
        
        return final_clip
        
    except Exception as e:
        print(f"Error in create_qa_video: {str(e)}")
        raise 