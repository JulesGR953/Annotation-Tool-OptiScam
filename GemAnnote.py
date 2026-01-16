import os
import json
import time
import typing_extensions as typing
from pathlib import Path
import google.generativeai as genai
from google.api_core import exceptions
import streamlit as st
from datetime import datetime

# === CONFIGURATION ===
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyDlpN6Q_P2sv10wZ89aD5l87BJPRI6JAB0"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyBGYrmJAiFc3AnEIuAElnNPgQQArOyJ-PQ"),
    os.getenv("GEMINI_API_KEY_3", "AIzaSyCXAQwbwO928YgRL1hCnJeDoelO-z0fFSE"),
    os.getenv("GEMINI_API_KEY_4", "AIzaSyCF2ieGA_lQzndShA7cvmyOsvE921UqqWQ"),
    os.getenv("GEMINI_API_KEY_5", "AIzaSyAb3CDDF0Y1XOAYkxZOmFYj66a1UO1mf6E"),
]


MODEL_NAME = "gemini-3-flash-preview"

SCAM_CRITERIA_TEXT = """
1. Commit Crime: Claims to commit a crime (e.g., hacking) for the user.
2. Unbounded Giveaway: Promises unlimited free items/currency without rules.
3. Bait and Switch: Promises content but redirects off-site immediately.
4. Off-Platform Traffic: Lures clicks off YouTube by promising fast money.
5. Malware/Phishing: Directs to sites that gather personal info or malware.
6. Get Rich Quick: Offers pyramid schemes or unrealistic financial gains.
7. Impersonation: Poses as a company or famous individual.
8. Generator Scams: Promises free gift cards while using generator tools.
"""

# === GEMINI FILE API FUNCTIONS ===

def switch_api_key():
    """Rotate to the next API key"""
    current_idx = st.session_state.current_api_index
    current_idx = (current_idx + 1) % len(API_KEYS)
    st.session_state.current_api_index = current_idx
    genai.configure(api_key=API_KEYS[current_idx])
    st.session_state.model = genai.GenerativeModel(MODEL_NAME)
    return current_idx + 1

def upload_video_to_gemini(video_path, max_retries=3):
    """Upload video to Gemini File API and wait for processing"""
    for attempt in range(max_retries):
        try:
            st.info(f"📤 Uploading video to Gemini... (Attempt {attempt + 1}/{max_retries})")
            
            # Upload the file
            video_file = genai.upload_file(path=str(video_path))
            st.success(f"✅ Upload initiated: {video_file.name}")
            
            # Poll until the file is processed (state = ACTIVE)
            with st.spinner("⏳ Waiting for Gemini to process video..."):
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                if video_file.state.name == "ACTIVE":
                    st.success("✅ Video processed and ready!")
                    return video_file
                else:
                    st.error(f"❌ File processing failed with state: {video_file.state.name}")
                    return None
                    
        except exceptions.ResourceExhausted:
            st.warning(f"⚠️ Rate limit hit on API key #{st.session_state.current_api_index + 1}")
            key_num = switch_api_key()
            st.info(f"🔄 Switched to API key #{key_num}")
            time.sleep(2)
            
        except Exception as e:
            st.error(f"❌ Upload error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return None
    
    return None

def cleanup_gemini_file(file_name):
    """Delete file from Gemini cloud storage"""
    try:
        genai.delete_file(file_name)
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not delete file {file_name}: {e}")
        return False

# MODIFIED: Accepts override_label to force the AI's perspective
def generate_reasoning_with_video(entry, video_file, model, override_label=None):
    """Generate AI reasoning using uploaded video file"""
    
    # Logic: If user selected a button, use that. Otherwise, check metadata loosely.
    if override_label:
        is_scam = (override_label == "Scam")
    else:
        raw_label = str(entry.get("label", "")).strip().lower()
        is_scam = "scam" in raw_label

    title = entry.get("title", "No Title")
    desc = entry.get("description", "No Description")

    if is_scam:
        # Aggressive PROSECUTOR prompt
        prompt = f"""Task: Analyze this YouTube video, its Title, and its Description.
        
Metadata Title: "{title}"
Metadata Description: "{desc}"

This content is a SCAM. 
Explain WHY the Video, Title, and Description are deceptive based on these criteria:
{SCAM_CRITERIA_TEXT}

Your Output:
Provide a clear, detailed explanation of the deception found in the video visuals, audio, and metadata. Be direct.(3-4 Sentences)"""
    else:
        # DEFENDER prompt
        prompt = f"""Task: Analyze this YouTube video, its Title, and its Description.

Metadata Title: "{title}"
Metadata Description: "{desc}"

This content has been identified as NON-SCAM (Legitimate).
Explain WHY the Video, Title, and Description appear safe and legitimate.

Your Output:
Provide a brief summary emphasizing the legitimate nature of the content.(3-4 Sentences)"""

    class ReasoningResponse(typing.TypedDict):
        reasoning: str

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [prompt, video_file],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ReasoningResponse
                )
            )
            return json.loads(response.text)["reasoning"]
            
        except exceptions.ResourceExhausted:
            st.warning(f"⚠️ Rate limit hit (attempt {attempt + 1})")
            key_num = switch_api_key()
            st.info(f"🔄 Switched to API key #{key_num}")
            model = st.session_state.model
            time.sleep(2)
            
        except exceptions.InternalServerError:
            st.warning(f"⚠️ Server error. Retrying in 5s... (attempt {attempt + 1})")
            time.sleep(5)
            
        except Exception as e:
            st.error(f"❌ Error generating reasoning: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return None
    
    return None

# === DATA LOADING FUNCTIONS ===

def load_metadata(path_str):
    """Load metadata from JSON files"""
    path = Path(path_str)
    all_data = []
    
    files_to_process = []
    if path.is_file():
        files_to_process.append(path)
    elif path.is_dir():
        files_to_process.extend(path.glob("*.json"))
    
    for json_file in files_to_process:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict):
                        all_data.append(data)
                    elif isinstance(data, list):
                        all_data.extend(data)
                except json.JSONDecodeError:
                    f.seek(0)
                    for line in f:
                        if line.strip():
                            all_data.append(json.loads(line))
        except Exception as e:
            st.error(f"Error reading {json_file}: {e}")

    return all_data

def get_video_files(video_dir):
    """Get all video files from directory"""
    video_dir = Path(video_dir)
    video_files = {}
    for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
        for f in video_dir.rglob(ext):
            video_files[f.stem] = f
    return video_files

def load_existing_data(output_path):
    """Load existing annotated data"""
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                processed_ids = {x['id'] for x in existing_data}
                return existing_data, processed_ids
        except:
            return [], set()
    return [], set()

def save_training_data(output_path, training_data):
    """Save training data to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# === STREAMLIT APP ===

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'current_api_index' not in st.session_state:
        st.session_state.current_api_index = 0
        genai.configure(api_key=API_KEYS[0])
        st.session_state.model = genai.GenerativeModel(MODEL_NAME)
    
    if 'training_data' not in st.session_state:
        st.session_state.training_data = []
    
    if 'processed_ids' not in st.session_state:
        st.session_state.processed_ids = set()
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    
    if 'current_entry' not in st.session_state:
        st.session_state.current_entry = None
    
    if 'current_video_file' not in st.session_state:
        st.session_state.current_video_file = None
    
    if 'ai_reasoning' not in st.session_state:
        st.session_state.ai_reasoning = ""
    
    if 'gemini_file' not in st.session_state:
        st.session_state.gemini_file = None
    
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = []
    
    if 'video_files' not in st.session_state:
        st.session_state.video_files = {}
    
    if 'skipped_count' not in st.session_state:
        st.session_state.skipped_count = 0

def load_next_video():
    """Load the next unprocessed video"""
    while st.session_state.current_index < len(st.session_state.raw_data):
        entry = st.session_state.raw_data[st.session_state.current_index]
        vid_id = entry.get("video_id")
        
        # Skip if already processed
        if vid_id in st.session_state.processed_ids:
            st.session_state.current_index += 1
            continue
        
        # Find matching video file
        matching_file = None
        for fname, fpath in st.session_state.video_files.items():
            if vid_id in fname:
                matching_file = fpath
                break
        
        if not matching_file:
            st.session_state.current_index += 1
            continue
        
        # Found a valid entry
        st.session_state.current_entry = entry
        st.session_state.current_video_file = matching_file
        st.session_state.ai_reasoning = ""
        st.session_state.gemini_file = None
        return True
    
    # No more videos
    st.session_state.current_entry = None
    st.session_state.current_video_file = None
    return False

# MODIFIED: Now checks the Radio Button for overrides
def generate_ai_reasoning():
    """Generate AI reasoning for current video"""
    if st.session_state.current_video_file and st.session_state.current_entry:
        video_file = upload_video_to_gemini(st.session_state.current_video_file)
        
        if video_file:
            st.session_state.gemini_file = video_file
            
            # Check for Manual Override from GUI
            manual_label = st.session_state.get("label_selector", "Auto")
            override = manual_label if manual_label != "Auto" else None

            with st.spinner(f"🤖 AI is analyzing as [{manual_label}]..."):
                reasoning = generate_reasoning_with_video(
                    st.session_state.current_entry,
                    video_file,
                    st.session_state.model,
                    override_label=override
                )
            
            if reasoning:
                # Calculate the final label for the output text
                if override:
                    final_label = override
                else:
                    raw_label = str(st.session_state.current_entry.get("label", "")).strip().lower()
                    final_label = "Scam" if "scam" in raw_label else "Legit"
                
                # Format: "Yes. [Reasoning]" or "No. [Reasoning]"
                prefix = "Yes" if final_label == "Scam" else "No"
                full_response = f"{prefix}. {reasoning}"
                
                # Update State and Widget
                st.session_state.ai_reasoning = full_response
                st.session_state['reasoning_editor'] = full_response
                
                st.success(f"✅ Reasoning Generated ({final_label})")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Failed to generate reasoning")
        else:
            st.error("❌ Failed to upload video")

def accept_and_save():
    """Accept the current reasoning and save to training data"""
    entry = st.session_state.current_entry
    reasoning = st.session_state.ai_reasoning
    
    if not reasoning.strip():
        st.error("⚠️ Please generate or enter reasoning before accepting")
        return
    
    # Create training entry
    user_prompt = f"Title: {entry.get('title', '')}\nDescription: {entry.get('description', '')}\n\nIs this video likely a Scam and Check if the Video is a Scam and the Title and Description are Deceptive? Answer Yes/No followed by your reasoning. 4-5 Sentences"
    
    # UPDATED: We use the reasoning exactly as it appears in the text box (which now includes Yes/No)
    sft_entry = {
        "id": entry.get("video_id"),
        "video": st.session_state.current_video_file.name,
        "conversations": [
            {"from": "human", "value": f"<video>\n{user_prompt}"},
            {"from": "response", "value": reasoning} 
        ]
    }
    
    st.session_state.training_data.append(sft_entry)
    st.session_state.processed_ids.add(entry.get("video_id"))
    
    # Save to file
    output_path = st.session_state.output_path
    if save_training_data(output_path, st.session_state.training_data):
        st.success(f"✅ Saved! Total annotated: {len(st.session_state.training_data)}")
    
    # Cleanup Gemini file
    if st.session_state.gemini_file:
        cleanup_gemini_file(st.session_state.gemini_file.name)
    
    # Move to next video
    st.session_state.current_index += 1
    load_next_video()
    st.rerun()

def skip_video():
    """Skip the current video"""
    st.session_state.skipped_count += 1
    
    # Cleanup Gemini file
    if st.session_state.gemini_file:
        cleanup_gemini_file(st.session_state.gemini_file.name)
    
    # Move to next video
    st.session_state.current_index += 1
    load_next_video()
    st.rerun()

def main():
    st.set_page_config(page_title="Scam Detection Annotation Tool", layout="wide")
    
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        
        video_folder = st.text_input(
            "Video Folder",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\GiftCard_Scams\videos\youtube"
        )
        
        metadata_folder = st.text_input(
            "Metadata Folder",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\GiftCard_Scams\metadata\youtube"
        )
        
        output_path = st.text_input(
            "Output File",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\sft_dataset_hitl.json"
        )
        
        st.session_state.output_path = output_path
        
        if st.button("🔄 Load Data", use_container_width=True):
            with st.spinner("Loading metadata and video files..."):
                st.session_state.raw_data = load_metadata(metadata_folder)
                st.session_state.video_files = get_video_files(video_folder)
                st.session_state.training_data, st.session_state.processed_ids = load_existing_data(output_path)
                st.session_state.current_index = 0
                load_next_video()
            st.success(f"✅ Loaded {len(st.session_state.raw_data)} metadata entries")
            st.rerun()
        
        st.divider()
        
        # Progress stats
        st.subheader("📊 Progress")
        total = len(st.session_state.raw_data)
        processed = len(st.session_state.training_data)
        remaining = total - processed - st.session_state.skipped_count
        
        st.metric("Total Videos", total)
        st.metric("Annotated", processed)
        st.metric("Skipped", st.session_state.skipped_count)
        st.metric("Remaining", remaining)
        
        if total > 0:
            progress = processed / total
            st.progress(progress)
            st.write(f"{progress*100:.1f}% Complete")
        
        st.divider()
        st.caption(f"API Key: #{st.session_state.current_api_index + 1}/{len(API_KEYS)}")
    
    # Main area
    st.title("🎬 Scam Detection Video Annotation")
    
    if st.session_state.current_entry is None:
        st.info("👈 Please load data from the sidebar to begin annotation")
        return
    
    entry = st.session_state.current_entry
    video_file = st.session_state.current_video_file
    
    # Video player and metadata
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 Video Player")
        if video_file and video_file.exists():
            st.video(str(video_file))
        else:
            st.warning("Video file not found")
    
    with col2:
        st.subheader("📋 Metadata")
        st.write(f"**Video ID:** {entry.get('video_id', 'N/A')}")
        st.write(f"**Label:** `{entry.get('label', 'N/A')}`")
        st.write(f"**Title:**")
        st.info(entry.get('title', 'N/A'))
        st.write(f"**Description:**")
        with st.expander("View Description"):
            st.write(entry.get('description', 'N/A'))
    
    st.divider()
    
    # AI Reasoning section
    st.subheader("🤖 AI Reasoning (Yes/No included)")

    # NEW: Manual Override Button
    current_meta_label = entry.get('label', 'Unknown')
    st.caption(f"Metadata thinks this is: {current_meta_label}")
    
    label_choice = st.radio(
        "Force AI Perspective:",
        ["Auto", "Scam", "Legit"],
        horizontal=True,
        key="label_selector",
        help="Select 'Scam' to force the AI to write a critique, or 'Legit' to write a defense."
    )
    
    # Generate button
    if st.button("🔮 Generate AI Reasoning", type="primary", use_container_width=True):
        generate_ai_reasoning()
    
    # Editable reasoning text area
    reasoning_text = st.text_area(
        "Response (Edit if needed)",
        value=st.session_state.ai_reasoning,
        height=200,
        key="reasoning_editor",
        help="This is exactly what will be saved to the JSON"
    )
    
    # Update session state with edited text
    st.session_state.ai_reasoning = reasoning_text
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Accept & Save", type="primary", use_container_width=True):
            accept_and_save()
    
    with col2:
        if st.button("⏭️ Skip", use_container_width=True):
            skip_video()
    
    with col3:
        if st.button("🔄 Regenerate", use_container_width=True):
            generate_ai_reasoning()

if __name__ == "__main__":
    main()