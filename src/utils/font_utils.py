import os
from pathlib import Path

def get_font_path(font_name, settings):
    """Get the full path for a font name"""
    # Get the project root directory (2 levels up from utils)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_fonts_dir = os.path.join(project_root, 'fonts')
    
    # Special handling for Phosphate font
    if font_name == "Phosphate-Solid":
        phosphate_paths = [
            os.path.join(local_fonts_dir, "Phosphate.ttc"),  # Check local fonts first
            "/System/Library/Fonts/Supplemental/Phosphate.ttc",
            "/Library/Fonts/Phosphate.ttc",
        ]
        for path in phosphate_paths:
            if os.path.exists(path):
                print(f"Found Phosphate font at: {path}")
                # Return just the font name for Phosphate-Solid
                return "Phosphate-Solid"
    
    # List of common font extensions
    font_extensions = ['.ttf', '.otf', '.TTF', '.OTF', '.ttc', '.TTC']
    
    # Get font directories from settings, prioritize local fonts directory
    font_directories = [local_fonts_dir] + settings.get('font_directories', [
        '/Library/Fonts/',  # macOS
        '/System/Library/Fonts/',  # macOS System
        '/System/Library/Fonts/Supplemental/',  # macOS Supplemental
        'C:\\Windows\\Fonts\\',  # Windows
        '/usr/share/fonts/',  # Linux
    ])
    
    print(f"Searching for font '{font_name}' in directories: {font_directories}")
    print(f"Local fonts directory: {local_fonts_dir}")
    
    # Try to find the font
    for directory in font_directories:
        if not os.path.exists(directory):
            print(f"Directory does not exist: {directory}")
            continue
            
        print(f"Searching in directory: {directory}")
        # List all files in directory
        try:
            files = os.listdir(directory)
            print(f"Found {len(files)} files in {directory}")
        except Exception as e:
            print(f"Error reading directory {directory}: {str(e)}")
            continue
            
        # Try exact name with extensions
        for ext in font_extensions:
            font_path = os.path.join(directory, font_name + ext)
            if os.path.exists(font_path):
                print(f"Found font at: {font_path}")
                return font_path
        
        # Try case-insensitive search
        for file in files:
            file_base = os.path.splitext(file)[0].lower()
            font_name_lower = font_name.lower()
            
            # Check exact match
            if file_base == font_name_lower:
                font_path = os.path.join(directory, file)
                print(f"Found font at: {font_path}")
                return font_path
    
    # If font not found, try to use a default system font
    default_fonts = [
        'Helvetica.ttf',
        'Arial.ttf',
        'DejaVuSans.ttf',
        'LucidaGrande.ttc',
        'HelveticaNeue.ttc'
    ]
    
    print(f"Font '{font_name}' not found, trying default fonts...")
    
    for default_font in default_fonts:
        for directory in font_directories:
            font_path = os.path.join(directory, default_font)
            if os.path.exists(font_path):
                print(f"Using default font: {font_path}")
                return font_path
    
    # If no font found, raise an error
    raise ValueError(f"Could not find font '{font_name}' or any default fonts") 