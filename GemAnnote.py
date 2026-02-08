import os
import json
import time
import typing_extensions as typing
from pathlib import Path
import google.generativeai as genai
from google.api_core import exceptions
import streamlit as st
from datetime import datetime
import cv2
import numpy as np

# === CONFIGURATION ===
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyALdQCpRvYKqvDkXuq_0wLsDIRQEpkGvZo"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyB__20hU9T5z7qUehgkkTG2nVRJa-TUFNA"),
    os.getenv("GEMINI_API_KEY_3", "AIzaSyDQR4rhnS8jZf_v4I032NANijlsfPU4As8"),
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

# === VIDEO FRAME EXTRACTION FUNCTIONS ===

def extract_frames_1fps(video_path, output_dir, video_id):
    """
    Extract ALL frames at 1 FPS and save with VLM training format: {video_id}_1.png, {video_id}_2.png, etc.
    For example: Video_ID_1_1.png, Video_ID_1_2.png, Video_ID_1_3.png
    Returns a list of frame file paths.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        st.error(f"Failed to open video: {video_path}")
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    # Sample at 1 fps
    frame_interval = int(fps) if fps > 0 else 30
    
    frame_paths = []
    frame_count = 0
    frame_number = 1  # Frame number for naming
    
    st.info(f"📹 Processing video: {video_path.name} (Duration: {duration:.1f}s, FPS: {fps:.1f})")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract one frame per second
        if frame_count % frame_interval == 0:
            # VLM training format: {video_id}_{frame_number}.png
            # Example: Video_ID_1_1.png, Video_ID_1_2.png, etc.
            frame_filename = f"{video_id}_{frame_number}.png"
            frame_path = output_dir / frame_filename
            
            # Save frame as PNG
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(str(frame_path))
            
            frame_number += 1
            
            # Update progress
            progress = min(frame_count / total_frames, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Extracted {len(frame_paths)} frames at 1 FPS ({progress*100:.1f}%)")
        
        frame_count += 1
    
    cap.release()
    
    if not frame_paths:
        st.warning("No frames extracted from video")
        return []
    
    st.success(f"✅ Extracted {len(frame_paths)} frames at 1 FPS in VLM format")
    
    progress_bar.empty()
    status_text.empty()
    
    return frame_paths

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

def upload_image_to_gemini(image_path, max_retries=3):
    """Upload image to Gemini File API and wait for processing"""
    for attempt in range(max_retries):
        try:
            st.info(f"📤 Uploading image to Gemini... (Attempt {attempt + 1}/{max_retries})")
            
            # Upload the file
            image_file = genai.upload_file(path=str(image_path))
            st.success(f"✅ Upload initiated: {image_file.name}")
            
            # Poll until the file is processed (state = ACTIVE)
            with st.spinner("⏳ Waiting for Gemini to process image..."):
                while image_file.state.name == "PROCESSING":
                    time.sleep(1)
                    image_file = genai.get_file(image_file.name)
                
                if image_file.state.name == "ACTIVE":
                    st.success("✅ Image processed and ready!")
                    return image_file
                else:
                    st.error(f"❌ File processing failed with state: {image_file.state.name}")
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
        prompt = f"""Task: Analyze this video, Title, and Description.
        
Metadata Title: "{title}"
Metadata Description: "{desc}"

This content is a SCAM. 
Explain WHY the video, Title, and Description are deceptive based on these criteria:
{SCAM_CRITERIA_TEXT}

Your Output:
Provide a clear, detailed explanation of the deception found in the visual content and metadata. Be direct.(3-4 Sentences)"""
    else:
        # DEFENDER prompt
        prompt = f"""Task: Analyze this video, Title, and Description.

Metadata Title: "{title}"
Metadata Description: "{desc}"

This content has been identified as NON-SCAM (Legitimate).
Explain WHY the video, Title, and Description appear safe and legitimate.

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

def generate_reasoning_with_frames(entry, frame_files, model, override_label=None):
    """Generate AI reasoning using uploaded frame files"""
    
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
        prompt = f"""Task: Analyze these video frames, Title, and Description.
        
Metadata Title: "{title}"
Metadata Description: "{desc}"

This content is a SCAM. 
Explain WHY the frames, Title, and Description are deceptive based on these criteria:
{SCAM_CRITERIA_TEXT}

Your Output:
Provide a clear, detailed explanation of the deception found in the visual content and metadata. Be direct.(3-4 Sentences)"""
    else:
        # DEFENDER prompt
        prompt = f"""Task: Analyze these video frames, Title, and Description.

Metadata Title: "{title}"
Metadata Description: "{desc}"

This content has been identified as NON-SCAM (Legitimate).
Explain WHY the frames, Title, and Description appear safe and legitimate.

Your Output:
Provide a brief summary emphasizing the legitimate nature of the content.(3-4 Sentences)"""

    class ReasoningResponse(typing.TypedDict):
        reasoning: str

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Build content list with prompt and all frame files
            content = [prompt] + frame_files
            
            response = model.generate_content(
                content,
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

def save_training_data(output_path, data):
    """Save training data to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# === SESSION STATE ===

def initialize_session_state():
    """Initialize all session state variables"""
    if 'current_api_index' not in st.session_state:
        st.session_state.current_api_index = 0
        genai.configure(api_key=API_KEYS[0])
        st.session_state.model = genai.GenerativeModel(MODEL_NAME)
    
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = []
    
    if 'video_files' not in st.session_state:
        st.session_state.video_files = {}
    
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
    
    if 'current_frame_files' not in st.session_state:
        st.session_state.current_frame_files = []
    
    if 'gemini_files' not in st.session_state:
        st.session_state.gemini_files = []
    
    if 'ai_reasoning' not in st.session_state:
        st.session_state.ai_reasoning = ""
    
    if 'skipped_count' not in st.session_state:
        st.session_state.skipped_count = 0
    
    if 'output_path' not in st.session_state:
        st.session_state.output_path = ""
    
    if 'frames_dir' not in st.session_state:
        st.session_state.frames_dir = ""

def load_next_video():
    """Load next unprocessed video"""
    while st.session_state.current_index < len(st.session_state.raw_data):
        entry = st.session_state.raw_data[st.session_state.current_index]
        video_id = entry.get("video_id")
        
        if video_id not in st.session_state.processed_ids:
            video_file = st.session_state.video_files.get(video_id)
            
            if video_file and video_file.exists():
                st.session_state.current_entry = entry
                st.session_state.current_video_file = video_file
                st.session_state.current_frame_files = []
                st.session_state.gemini_files = []
                st.session_state.ai_reasoning = ""
                return
        
        st.session_state.current_index += 1
    
    st.session_state.current_entry = None
    st.session_state.current_video_file = None

# === ANNOTATION FUNCTIONS ===

def generate_ai_reasoning():
    """Upload video to Gemini for reasoning, then extract frames locally for VLM dataset"""
    entry = st.session_state.current_entry
    video_file = st.session_state.current_video_file
    
    # Get override choice
    override = None
    if st.session_state.get('label_selector') != "Auto":
        override = st.session_state.label_selector
    
    # Step 1: Upload VIDEO to Gemini and generate reasoning
    st.info("Step 1: Uploading video to Gemini for reasoning...")
    gemini_video_file = upload_video_to_gemini(video_file)
    
    if gemini_video_file:
        st.session_state.gemini_files = [gemini_video_file]
        
        # Generate reasoning from the video
        reasoning = generate_reasoning_with_video(
            entry,
            gemini_video_file,
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
            
            # Step 2: Extract frames locally at 1 FPS for VLM training dataset
            st.info("Step 2: Extracting frames at 1 FPS for VLM training dataset...")
            
            # Use the ACTUAL video_id from metadata (e.g., "youtube__fBs4O6qzVE")
            video_id = entry.get("video_id")
            
            # Create a separate folder for this video's frames
            frames_base_dir = Path(st.session_state.frames_dir)
            video_frames_dir = frames_base_dir / video_id
            
            frame_paths = extract_frames_1fps(video_file, video_frames_dir, video_id)
            
            if frame_paths:
                st.session_state.current_frame_files = frame_paths
                st.success(f"✅ Extracted {len(frame_paths)} frames for VLM dataset in folder: {video_id}")
            else:
                st.warning("⚠️ Failed to extract frames, but reasoning was generated")
            
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
    frame_files = st.session_state.current_frame_files
    
    if not reasoning.strip():
        st.error("⚠️ Please generate or enter reasoning before accepting")
        return
    
    if not frame_files:
        st.error("⚠️ No frames available. Please generate reasoning first.")
        return
    
    # Use the ACTUAL video_id from metadata (e.g., "youtube__fBs4O6qzVE")
    video_id = entry.get("video_id")
    
    # Create user prompt (NO image tags!)
    user_prompt = f"Title: {entry.get('title', '')}\nDescription: {entry.get('description', '')}\n\nIs this video likely a Scam and Check if the Video is a Scam and the Title and Description are Deceptive? Answer Yes/No followed by your reasoning. 4-5 Sentences"
    
    sft_entry = {
        "id": video_id,
        "images": [str(Path(fp).name) for fp in frame_files],  # Just the filenames: youtube__fBs4O6qzVE_1.png, youtube__fBs4O6qzVE_2.png, etc.
        "conversations": [
            {"from": "human", "value": user_prompt},
            {"from": "response", "value": reasoning}
        ]
    }
    
    st.session_state.training_data.append(sft_entry)
    st.session_state.processed_ids.add(video_id)
    
    # Save to file
    output_path = st.session_state.output_path
    if save_training_data(output_path, st.session_state.training_data):
        st.success(f"✅ Saved as {video_id}! Total annotated: {len(st.session_state.training_data)}")
    
    # Cleanup Gemini files
    for gemini_file in st.session_state.gemini_files:
        cleanup_gemini_file(gemini_file.name)
    
    # Move to next video
    st.session_state.current_index += 1
    load_next_video()
    st.rerun()
    for gemini_file in st.session_state.gemini_files:
        cleanup_gemini_file(gemini_file.name)
    
    # Move to next video
    st.session_state.current_index += 1
    load_next_video()
    st.rerun()

def skip_video():
    """Skip the current video"""
    st.session_state.skipped_count += 1
    
    # Cleanup Gemini files
    for gemini_file in st.session_state.gemini_files:
        cleanup_gemini_file(gemini_file.name)
    
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
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\Crypto Scams\videos\Youtube"
        )
        
        metadata_folder = st.text_input(
            "Metadata Folder",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\Crypto Scams\metadata\youtube"
        )
        
        frames_folder = st.text_input(
            "Frames Output Folder",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\extracted_frames"
        )
        
        output_path = st.text_input(
            "Output File",
            value=r"C:\Users\Jules Gregory\Desktop\GemAnnote\CrytoScams_Youtube.json"
        )
        
        st.session_state.output_path = output_path
        st.session_state.frames_dir = frames_folder
        
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
    st.title("🎬 Scam Detection Video Annotation (1 FPS Frame Extraction)")
    
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
        
        # Display extracted frames
        if st.session_state.current_frame_files:
            st.subheader(f"🖼️ Extracted Frames ({len(st.session_state.current_frame_files)} frames at 1 FPS)")
            # Show frames in a grid (3 columns)
            cols_per_row = 3
            for i in range(0, len(st.session_state.current_frame_files), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(st.session_state.current_frame_files):
                        frame_path = st.session_state.current_frame_files[i + j]
                        col.image(frame_path, caption=Path(frame_path).name, use_container_width=True)
    
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

    # Manual Override Button
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