Instructions to Run the Scam Detection Annotation Tool
Prerequisites
1. Install Required Software

Python 3.8+ (Download from python.org)
pip (usually comes with Python)

2. Install Required Python Packages
Open a terminal/command prompt and run:
bashpip install streamlit google-generativeai typing-extensions
Configuration
1. Set Up Gemini API Keys
You need Google Gemini API keys. Get them from Google AI Studio.
Option A: Set Environment Variables (Recommended)
Windows (Command Prompt):
cmdset GEMINI_API_KEY_1=your_first_api_key_here
set GEMINI_API_KEY_2=your_second_api_key_here
set GEMINI_API_KEY_3=your_third_api_key_here
set GEMINI_API_KEY_4=your_fourth_api_key_here
set GEMINI_API_KEY_5=your_fifth_api_key_here
Windows (PowerShell):
powershell$env:GEMINI_API_KEY_1="your_first_api_key_here"
$env:GEMINI_API_KEY_2="your_second_api_key_here"
$env:GEMINI_API_KEY_3="your_third_api_key_here"
$env:GEMINI_API_KEY_4="your_fourth_api_key_here"
$env:GEMINI_API_KEY_5="your_fifth_api_key_here"
Mac/Linux:
bashexport GEMINI_API_KEY_1="your_first_api_key_here"
export GEMINI_API_KEY_2="your_second_api_key_here"
export GEMINI_API_KEY_3="your_third_api_key_here"
export GEMINI_API_KEY_4="your_fourth_api_key_here"
export GEMINI_API_KEY_5="your_fifth_api_key_here"
Option B: Edit the Code Directly
In the Python file, replace "KEY1", "KEY2", etc. with your actual API keys:
pythonAPI_KEYS = [
    "your_actual_api_key_1",
    "your_actual_api_key_2",
    "your_actual_api_key_3",
    "your_actual_api_key_4",
    "your_actual_api_key_5",
]
```

### 2. Prepare Your Data Structure

Organize your files as follows:
```
project_folder/
├── videos/
│   └── youtube/
│       ├── video1.mp4
│       ├── video2.mp4
│       └── ...
├── metadata/
│   └── youtube/
│       ├── video1.json
│       ├── video2.json
│       └── ...
└── output/
Metadata JSON Format:
Each JSON file should contain:
json{
  "video_id": "unique_video_id",
  "title": "Video Title",
  "description": "Video Description",
  "label": "scam" or "legit"
}
Running the Application
1. Navigate to Your Project Folder
bashcd path/to/your/project/folder
2. Run Streamlit
bashstreamlit run your_script_name.py
Replace your_script_name.py with the actual filename (e.g., annotate.py).
3. The App Will Open in Your Browser

Usually opens automatically at http://localhost:8501
If not, manually navigate to that URL

Using the Tool
Initial Setup (in Sidebar)

Video Folder: Enter the path to your videos folder

Example: C:\Users\YourName\Desktop\project\videos\youtube


Metadata Folder: Enter the path to your metadata folder

Example: C:\Users\YourName\Desktop\project\metadata\youtube


Output File: Enter where you want to save annotations

Example: C:\Users\YourName\Desktop\project\sft_dataset_hitl.json


Click "🔄 Load Data"

Annotation Workflow

Review the video in the video player
Check the metadata (title, description, original label)
Choose AI perspective (Auto/Scam/Legit):

Auto: Uses the metadata label
Scam: Forces AI to critique as scam
Legit: Forces AI to defend as legitimate


Click "🔮 Generate AI Reasoning"
Edit the response if needed in the text area
Click "✅ Accept & Save" to save, or "⏭️ Skip" to skip

Action Buttons

✅ Accept & Save: Saves current annotation and moves to next video
⏭️ Skip: Skips current video without saving
🔄 Regenerate: Generates new AI reasoning for current video

Troubleshooting
Rate Limit Errors

The tool automatically switches between API keys when rate limits are hit
Add more API keys if you encounter frequent rate limiting

Video Not Found

Ensure video filename contains the video_id from metadata
Check that video file extensions are supported (mp4, avi, mov, mkv)

JSON Errors

Verify metadata JSON files are properly formatted
Check for missing required fields (video_id, title, description, label)

Module Not Found
bashpip install --upgrade streamlit google-generativeai typing-extensions
Port Already in Use
bashstreamlit run your_script_name.py --server.port 8502
Output Format
The tool saves annotations to a JSON file with this structure:
json[
  {
    "id": "video_id",
    "video": "video_filename.mp4",
    "conversations": [
      {
        "from": "human",
        "value": "<video>\nTitle: ...\nDescription: ...\n\nIs this video likely a Scam..."
      },
      {
        "from": "response",
        "value": "Yes. [AI reasoning explaining why it's a scam]"
      }
    ]
  }
]
Tips

The tool automatically saves progress after each annotation
You can resume annotation by loading the same output file
Progress is tracked in the sidebar
Press Ctrl+C in the terminal to stop the application
