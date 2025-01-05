import json
import os

def load_settings():
    """Load settings and project settings"""
    # Get the root directory of the application
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Root directory: {root_dir}")
    
    # Load main settings file
    with open('settings.json', 'r') as file:
        main_settings = json.load(file)
    
    # Determine which format to use (standard or tiktok)
    if main_settings['tiktok']['enabled']:
        format_settings = main_settings['tiktok']
        print("Using TikTok format settings")
    elif main_settings['standard']['enabled']:
        format_settings = main_settings['standard']
        print("Using standard format settings")
    else:
        raise ValueError("Neither standard nor TikTok format is enabled in settings")
    
    # Get project paths
    project_settings_path = format_settings['project']
    project_dir = os.path.dirname(project_settings_path)
    print(f"Project directory: {project_dir}")
    
    # Store intro and end paths in project settings
    project_intro_path = format_settings.get('project_intro', '')
    project_end_path = format_settings.get('project_end', '')
    
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
        '/System/Library/Fonts/Supplemental/',  # macOS Supplemental
        'C:\\Windows\\Fonts\\',  # Windows
        '/usr/share/fonts/',  # Linux
        os.path.join(os.path.dirname(__file__), 'fonts/')  # Local fonts directory
    ])
    
    # Add TikTok-specific settings if using TikTok format
    if main_settings['tiktok']['enabled']:
        project_settings['tiktok_output'] = main_settings['tiktok']['output']
    
    # Load questions
    questions_path = os.path.join(project_dir, project_settings['questions_file'])
    print(f"Questions path: {questions_path}")
    
    with open(questions_path, 'r') as file:
        questions_data = json.load(file)
    
    # Update paths to be relative to project directory for media files
    if 'background_image' in project_settings:
        if project_settings['background_image']:  # Only update if not empty
            project_settings['background_image'] = os.path.join(root_dir, project_settings['background_image'].lstrip('/'))
            print(f"Background image path: {project_settings['background_image']}")
    
    # Update audio paths
    if 'audio' in project_settings and 'file' in project_settings['audio']:
        audio_path = os.path.join(root_dir, project_settings['audio']['file'].lstrip('/'))
        project_settings['audio']['file'] = audio_path
        print(f"Audio file path: {project_settings['audio']['file']}")
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found at {audio_path}")
    
    if 'timer' in project_settings and 'sound' in project_settings['timer']:
        timer_sound_path = os.path.join(root_dir, project_settings['timer']['sound']['file'].lstrip('/'))
        project_settings['timer']['sound']['file'] = timer_sound_path
        print(f"Timer sound path: {project_settings['timer']['sound']['file']}")
        if not os.path.exists(timer_sound_path):
            print(f"Warning: Timer sound file not found at {timer_sound_path}")
    
    return project_settings, questions_data, project_dir 