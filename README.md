
# Scam Detection Video Annotation Tool 🕵️‍♂️🎬

A **Streamlit-based human-in-the-loop annotation tool** designed to create high-quality training datasets for scam video detection. This tool leverages Google's **Gemini API** to generate AI-assisted reasoning, which human annotators can review, edit, and validate before saving.

## ✨ Features

- **🎬 Video Playback:** Integrated video player with synchronized metadata display (Title, Description, etc.)
- **🤖 AI-Powered Reasoning:** Uses Google Gemini to automatically generate detailed explanations for why a video is (or isn't) a scam
- **✏️ Human-in-the-loop:** Fully editable AI responses allow you to refine the reasoning before saving
- **🔄 Robust API Handling:** Automatic API key rotation to handle rate limits seamlessly
- **📊 Live Progress Tracking:** Visual statistics on processed, skipped, and remaining videos
- **💾 Auto-Save & Resume:** Automatically saves your progress after every video. Resume right where you left off
- **🎯 Manual Override:** "Judge Mode" allows you to force the AI to adopt a specific perspective (Prosecutor vs. Defender) regardless of metadata labels

---

## 🛠️ Installation

### Prerequisites
- **Python 3.8** or higher
- **Google Gemini API Key(s)** - Get them from [Google AI Studio](https://aistudio.google.com/)

### Install Dependencies
```bash
pip install streamlit google-generativeai typing-extensions
```

## ⚙️ Setup

### 1. Configure API Keys

You can set up your API keys using either environment variables (recommended) or by editing the code directly.

**Option A: Environment Variables (Recommended)**

**Linux/Mac:**
```bash
export GEMINI_API_KEY_1="your_api_key_here"
export GEMINI_API_KEY_2="your_api_key_here"
# Add up to 5 keys if needed
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY_1="your_api_key_here"
$env:GEMINI_API_KEY_2="your_api_key_here"
```

**Windows Command Prompt:**
```cmd
set GEMINI_API_KEY_1=your_api_key_here
set GEMINI_API_KEY_2=your_api_key_here
```

**Option B: Edit Code Directly**

Open `GemAnnote.py` and modify the `API_KEYS` list at the top:
```python
API_KEYS = [
    "your_actual_api_key_1",
    "your_actual_api_key_2",
    # Add more keys as needed
]
```

### 2. Prepare Your Data

Organize your project files using the following structure:

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
```

**Metadata JSON Format:**
```json
{
  "video_id": "unique_identifier",
  "title": "Video Title",
  "description": "Video description text",
  "label": "scam"
}
```

**Required Fields:**
- `video_id` (required): Unique ID (must create a partial match with the video filename)
- `title` (required): The video title
- `description` (required): The full video description
- `label`: "scam" or "legit" (Used for auto-detection)

---

## 🚀 Usage

### 1. Run the Application
```bash
streamlit run GemAnnote.py
```

The app will open automatically in your browser at `http://localhost:8501`.

### 2. Configure Paths (Sidebar)

- **Video Folder**: Path to your directory containing `.mp4` files
- **Metadata Folder**: Path to your directory containing `.json` files
- **Output File**: Path where the final annotated JSON will be saved
- Click **"🔄 Load Data"** to initialize

### 3. Annotation Workflow

1. **Watch the video** in the player
2. **Review the displayed metadata** (Title, Description)
3. **Select Perspective:**
   - `Auto`: Uses the metadata label to decide the prompt
   - `Scam`: Forces the AI to critique the video as a scam (Prosecutor mode)
   - `Legit`: Forces the AI to defend the video as legitimate (Defense mode)
4. **Generate**: Click **🔮 Generate AI Reasoning**
5. **Edit**: Modify the generated text in the text area if needed
6. **Decide:**
   - **✅ Accept & Save**: Saves the entry and loads the next video
   - **⏭️ Skip**: Ignores the current video and moves to the next
   - **🔄 Regenerate**: Re-runs the AI analysis

---

## 📂 Output Format

Annotations are saved in a JSON format compatible with SFT (Supervised Fine-Tuning) training pipelines (e.g., LLaVA, SmolVLM):

```json
[
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
```

---

## 🛡️ Scam Detection Criteria

The AI is prompted to evaluate videos based on the following specific criteria:

1. **Commit Crime**: Claims to commit crimes (e.g., hacking) for the user
2. **Unbounded Giveaway**: Promises unlimited free items without rules
3. **Bait and Switch**: Promises content but redirects off-site immediately
4. **Off-Platform Traffic**: Lures clicks with "fast money" promises
5. **Malware/Phishing**: Directs users to malicious sites
6. **Get Rich Quick**: Pyramid schemes or unrealistic financial gains
7. **Impersonation**: Poses as a known company or celebrity
8. **Generator Scams**: Fake gift card or currency generators

---

## 🔧 Troubleshooting

### Rate Limits
If you see rate limit warnings, add more keys to the `API_KEYS` list. The tool handles rotation automatically.

### Video Not Found
Ensure the `video_id` in your JSON is a substring of the actual video filename.

### JSON Parse Errors
Validate your metadata files at [jsonlint.com](https://jsonlint.com).

### Port Already in Use
```bash
streamlit run GemAnnote.py --server.port 8502
```

### Module Not Found
```bash
pip install --upgrade streamlit google-generativeai typing-extensions
```

---

## 💡 Tips

- Progress is auto-saved after each annotation
- The tool automatically skips already-processed videos when resuming
- Use manual override for edge cases where metadata labels are ambiguous
- Keep video files and metadata in sync using consistent naming

---

## 📝 License

MIT License. Feel free to modify and distribute.

---

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

---

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Note**: This tool requires an active internet connection to communicate with the Google Gemini API. Ensure you have sufficient API quota before starting large annotation sessions.


