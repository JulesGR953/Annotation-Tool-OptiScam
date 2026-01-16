# Scam Detection Video Annotation Tool 🕵️‍♂️🎬

A **Streamlit-based human-in-the-loop annotation tool** designed to create high-quality training datasets for scam video detection. This tool leverages Google's **Gemini 1.5 Flash API** to generate AI-assisted reasoning, which human annotators can review, edit, and validate before saving.

## ✨ Features

* **🎬 Video Playback:** Integrated video player with synchronized metadata display (Title, Description, etc.).
* **🤖 AI-Powered Reasoning:** Uses Google Gemini 1.5 Flash to automatically generate detailed explanations for why a video is (or isn't) a scam.
* **✏️ Human-in-the-loop:** Fully editable AI responses allow you to refine the reasoning before saving.
* **🔄 Robust API Handling:** Automatic API key rotation to handle rate limits seamlessly.
* **📊 Live Progress Tracking:** Visual statistics on processed, skipped, and remaining videos.
* **💾 Auto-Save & Resume:** Automatically saves your progress after every video. Resume right where you left off.
* **🎯 Manual Override:** "Judge Mode" allows you to force the AI to adopt a specific perspective (Prosecutor vs. Defender) regardless of metadata labels.

---

## 🛠️ Installation

### Prerequisites
* **Python 3.8** or higher
* **Google Gemini API Key(s)** - Get them from [Google AI Studio](https://aistudio.google.com/)

### Install Dependencies
```bash
pip install streamlit google-generativeai typing-extensions
