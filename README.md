Scam Detection Video Annotation Tool
A Streamlit-based human-in-the-loop annotation tool for creating training datasets to detect scam videos. Uses Google's Gemini API to generate AI-assisted reasoning that can be reviewed and edited before saving.
Features

🎬 Video playback with metadata display
🤖 AI-powered reasoning generation using Gemini
✏️ Editable AI responses before saving
🔄 Automatic API key rotation for rate limit handling
📊 Progress tracking and statistics
💾 Automatic save with resume capability
🎯 Manual label override (force AI perspective)

Installation
Prerequisites

Python 3.8 or higher
Google Gemini API key(s) - Get from Google AI Studio

Install Dependencies
bashpip install streamlit google-generativeai typing-extensions
Setup
1. Configure API Keys
Option A: Environment Variables (Recommended)
bash# Linux/Mac
export GEMINI_API_KEY_1="your_api_key_here"
export GEMINI_API_KEY_2="your_api_key_here"
export GEMINI_API_KEY_3="your_api_key_here"
export GEMINI_API_KEY_4="your_api_key_here"
export GEMINI_API_KEY_5="your_api_key_here"

# Windows Command Prompt
set GEMINI_API_KEY_1=your_api_key_here
set GEMINI_API_KEY_2=your_api_key_here

# Windows PowerShell
$env:GEMINI_API_KEY_1="your_api_key_here"
$env:GEMINI_API_KEY_2="your_api_key_here"
Option B: Edit Code Directly
Modify the API_KEYS list in the script:
pythonAPI_KEYS = [
    "your_actual_api_key_1",
    "your_actual_api_key_2",
    # Add more keys as needed
]
```

### 2. Prepare Your Data

Organize files in this structure:
```
project/
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
    └── sft_dataset_hitl.json
Metadata JSON Format:
json{
  "video_id": "unique_identifier",
  "title": "Video Title",
  "description": "Video description text",
  "label": "scam"
}
Supported Fields:

video_id (required): Unique identifier (must match video filename)
title (required): Video title
description (required): Video description
label (required): "scam" or "legit"

Usage
1. Run the Application
bashstreamlit run annotate.py
The app will open in your browser at http://localhost:8501
2. Configure Paths (in sidebar)

Video Folder: Path to your videos directory
Metadata Folder: Path to your metadata JSON files
Output File: Path where annotations will be saved
Click "🔄 Load Data"

3. Annotation Workflow

Watch the video in the player
Review metadata (title, description, label)
Select AI perspective:

Auto: Uses metadata label
Scam: Forces AI to critique as scam
Legit: Forces AI to defend as legitimate


Generate reasoning: Click "🔮 Generate AI Reasoning"
Edit if needed: Modify the AI response in the text area
Save or skip:

✅ Accept & Save: Save annotation and move to next
⏭️ Skip: Skip without saving
🔄 Regenerate: Generate new reasoning



4. Output Format
Annotations are saved in this format:
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
        "value": "Yes. The video uses deceptive tactics including..."
      }
    ]
  }
]
Scam Detection Criteria
The AI evaluates videos based on these criteria:

Commit Crime: Claims to commit crimes (e.g., hacking)
Unbounded Giveaway: Promises unlimited free items without rules
Bait and Switch: Promises content but redirects off-site
Off-Platform Traffic: Lures clicks with fast money promises
Malware/Phishing: Directs to malicious sites
Get Rich Quick: Pyramid schemes or unrealistic gains
Impersonation: Poses as companies or celebrities
Generator Scams: Fake gift card generators

Features in Detail
Automatic API Key Rotation

Automatically switches to next API key when rate limits are hit
Supports up to 5 API keys for extended annotation sessions

Progress Tracking

Total videos count
Annotated count
Skipped count
Remaining videos
Progress percentage

Resume Capability

Load existing output file to continue annotation
Automatically skips already processed videos

Manual Override

Force AI to analyze from "Scam" or "Legit" perspective
Useful when metadata label is incorrect or ambiguous

Troubleshooting
Rate Limits

Add more API keys to API_KEYS list
Tool automatically rotates through available keys

Video Not Found

Ensure video filename contains the video_id
Check file extensions: .mp4, .avi, .mov, .mkv

JSON Parse Errors

Validate JSON format using jsonlint.com
Ensure all required fields are present

Port Already in Use
bashstreamlit run annotate.py --server.port 8502
Module Errors
bashpip install --upgrade streamlit google-generativeai typing-extensions
Configuration Options
Edit these variables in the script to customize:
pythonMODEL_NAME = "gemini-3-flash-preview"  # Gemini model to use
SCAM_CRITERIA_TEXT = """..."""          # Scam detection criteria
Tips

Progress is auto-saved after each annotation
Use keyboard shortcuts for faster workflow
Review AI reasoning carefully before accepting
Use manual override for edge cases
Keep video files and metadata in sync

License
MIT License - feel free to modify and distribute
Contributing
Contributions welcome! Please open an issue or submit a pull request.
Support
For issues or questions, please open a GitHub issue.

Note: This tool requires active internet connection for Gemini API calls. Ensure you have sufficient API quota before starting large annotation sessions.
