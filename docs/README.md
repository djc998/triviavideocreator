'll create a comprehensive README.md file for the root of the project:
project_root/
├── src/
│ ├── init.py
│ ├── main.py # Main entry point
│ ├── settings.py # Settings loading and management
│ ├── clip_creators/ # Video clip creation modules
│ │ ├── init.py
│ │ ├── text_clip.py # Text overlay creation
│ │ ├── timer_clip.py # Countdown timer creation
│ │ ├── qa_clip.py # Question/Answer clip creation
│ │ └── bookend_clip.py # Intro/End clip creation
│ └── utils/ # Utility functions
│ ├── init.py
│ ├── font_utils.py # Font handling
│ ├── position_utils.py # Position calculation
│ └── text_utils.py # Text processing
├── projects/ # Project configuration files
│ ├── template/ # Template project
│ │ ├── project_settings.json
│ │ ├── project_intro.json
│ │ ├── project_end.json
│ │ └── questions.json
│ └── tiktok/ # TikTok format template
└── settings.json # Global settings
json
json
{
"standard": {
"enabled": true,
"project": "projects/template/project_settings.json",
"project_intro": "projects/template/project_intro.json",
"project_end": "projects/template/project_end.json"
},
"tiktok": {
"enabled": false,
"project": "projects/template/tiktok/project_settings.json",
"output": {
"questions_per_video": 1,
"number_of_videos": 1,
"filename_prefix": "tiktok_part"
}
},
"font_directories": [
"/Library/Fonts/",
"/System/Library/Fonts/",
"C:\\Windows\\Fonts\\",
"/usr/share/fonts/",
"fonts/"
]
}
json
json
{
"questions_file": "questions.json",
"background": {
"color": "#060CE9",
"opacity": 1.0
},
"text": {
"font": "Phosphate-Solid",
"size": {
"question": 120,
"answer": 90,
"timer": 80
},
"color": "#FFFFFF",
"shadow": {
"enabled": true,
"color": "#000000",
"offset": {"x": 5, "y": 5}
},
"outline": {
"enabled": true,
"color": "#000000",
"thickness": 2
}
},
"timing": {
"question_duration": 10,
"answer_duration": 3
},
"video": {
"width": 1280,
"height": 720,
"fps": 24
}
}
:
bash
pip install moviepy numpy Pillow
:
bash
python src/main.py
json
"preview_mode": {
"enabled": true,
"type": "questions", // or "duration"
"questions_limit": 2,
"duration_limit": 30
}
json
"tiktok_output": {
"questions_per_video": 1,
"number_of_videos": 5,
"filename_prefix": "tiktok_part"
}
json
{
"questions": [
{
"question": "What is the capital of France?",
"answer": "Paris"
},
{
"question": "What is 2 + 2?",
"answer": "4"
}
]
}
:
json
"overlays": [
{
"content": "Follow @username",
"font": "Phosphate-Solid",
"size": 40,
"color": "#FFFFFF",
"position": {
"x": "right",
"y": "bottom",
"padding": 20
},
"timing": {
"start": 0,
"duration": "full",
"fade": {
"enabled": true,
"duration": 0.3
}
}
}
]
