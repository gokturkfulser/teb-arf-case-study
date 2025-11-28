import streamlit as st
import requests
import time
from io import BytesIO
import json
from typing import Optional, Dict, List
import os
from datetime import datetime

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TEB ARF STT-RAG",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_health() -> Dict:
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": "Service unavailable"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def text_query(question: str, k: int = 5) -> Optional[Dict]:
    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/text-query",
            json={"question": question, "k": k},
            timeout=60
        )
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Gateway service. Make sure services are running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The service may be processing a large query.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def voice_query(audio_file) -> Optional[Dict]:
    try:
        # Reset file pointer to beginning if it's a file-like object
        if hasattr(audio_file, 'seek'):
            audio_file.seek(0)
        
        # Get filename and content type
        filename = getattr(audio_file, 'name', 'recording.wav')
        content_type = getattr(audio_file, 'type', 'audio/wav')
        
        # Ensure content type is set correctly
        if not content_type or content_type == 'application/octet-stream':
            content_type = 'audio/wav'
        
        # Read file content
        audio_content = audio_file.read()
        
        # Verify we have content
        if not audio_content or len(audio_content) == 0:
            st.error("❌ Audio file is empty. Please record or upload a valid audio file.")
            return None
        
        files = {"file": (filename, audio_content, content_type)}
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/voice-query",
            files=files,
            timeout=120
        )
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Gateway service. Make sure services are running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Audio processing may take longer.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def transcribe_audio(audio_file) -> Optional[Dict]:
    try:
        # Reset file pointer to beginning if it's a file-like object
        if hasattr(audio_file, 'seek'):
            audio_file.seek(0)
        
        # Get filename and content type
        filename = getattr(audio_file, 'name', 'recording.wav')
        content_type = getattr(audio_file, 'type', 'audio/wav')
        
        # Ensure content type is set correctly
        if not content_type or content_type == 'application/octet-stream':
            content_type = 'audio/wav'
        
        # Read file content
        audio_content = audio_file.read()
        
        # Verify we have content
        if not audio_content or len(audio_content) == 0:
            st.error("❌ Audio file is empty. Please record or upload a valid audio file.")
            return None
        
        files = {"file": (filename, audio_content, content_type)}
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/transcribe",
            files=files,
            timeout=60
        )
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Gateway service. Make sure services are running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Audio processing may take longer.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def scrape_campaigns() -> Optional[Dict]:
    try:
        response = requests.post(f"{GATEWAY_URL}/api/v1/scrape", timeout=300)
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Gateway service. Make sure services are running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Scraping may take several minutes.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def index_campaigns() -> Optional[Dict]:
    try:
        response = requests.post(f"{GATEWAY_URL}/api/v1/index", timeout=600)
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Gateway service. Make sure services are running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Indexing may take several minutes.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def main():
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2ca02c, #1f77b4);
        transform: scale(1.02);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🎤 TEB ARF STT-RAG Integration</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Speech-to-Text & Retrieval-Augmented Generation for Campaign Queries</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("🔧 System Status")
        health_status = check_health()
        
        if health_status.get("status") == "healthy":
            st.success("✅ All Services Healthy")
            st.json(health_status)
        else:
            st.error("❌ Service Issues Detected")
            st.json(health_status)
        
        st.divider()
        
        st.header("⚙️ Settings")
        st.text_input("Gateway URL", value=GATEWAY_URL, disabled=True, help="Change via GATEWAY_URL environment variable")
        
        st.divider()
        
        st.header("📊 Quick Actions")
        if st.button("🔄 Refresh Health"):
            st.rerun()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Text Query", 
        "🎙️ Voice Query", 
        "📝 Transcribe", 
        "🔍 Scrape & Index",
        "📈 Statistics",
        "📜 Query History"
    ])
    
    with tab1:
        st.header("Text Query")
        st.markdown("Ask questions about campaigns using text input.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            question = st.text_input(
                "Enter your question",
                placeholder="e.g., iphone kampanyası nedir?",
                key="text_question"
            )
        
        with col2:
            k = st.number_input("Results", min_value=1, max_value=10, value=5, step=1)
        
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if question:
                start_time = time.time()
                with st.spinner("Searching..."):
                    result = text_query(question, k)
                    if result:
                        elapsed_time = time.time() - start_time
                        st.success(f"✅ Query completed! (Time: {elapsed_time:.2f}s)")
                        
                        # Save to history
                        if "query_history" not in st.session_state:
                            st.session_state.query_history = []
                        st.session_state.query_history.append({
                            "type": "Text Query",
                            "query": question,
                            "answer": result.get("answer", ""),
                            "sources": result.get("sources", []),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.markdown("### 📋 Answer")
                        answer_text = result.get("answer", "No answer")
                        with st.expander("📄 Answer", expanded=True):
                            st.write(answer_text)
                        
                        sources = result.get("sources", [])
                        if sources:
                            st.markdown(f"### 📚 Sources ({result.get('num_sources', 0)})")
                            
                            # Source score visualization
                            if len(sources) > 0:
                                score_data = {f"Source {i+1}": [s.get('score', 0)] for i, s in enumerate(sources)}
                                st.bar_chart(score_data)
                            
                            for i, source in enumerate(sources, 1):
                                with st.expander(f"📄 {i}. {source.get('title', 'Unknown')} (Score: {source.get('score', 0):.3f})"):
                                    st.write(f"**Campaign ID:** {source.get('campaign_id', 'N/A')}")
                                    st.write(f"**Score:** {source.get('score', 0):.4f}")
                                    if 'text' in source:
                                        st.write(f"**Text:** {source['text'][:200]}...")
            else:
                st.warning("Please enter a question")
    
    with tab2:
        st.header("Voice Query")
        st.markdown("Record audio or upload an audio file to get transcription and answer.")
        
        st.info("💡 **Tip:** For best transcription quality, speak clearly in a quiet environment. Uploaded files typically produce better results than browser recordings.")
        
        option = st.radio(
            "Choose input method:",
            ["🎤 Record Audio", "📁 Upload File"],
            horizontal=True
        )
        
        audio_file = None
        
        if option == "🎤 Record Audio":
            audio_input = st.audio_input("Record your question")
            if audio_input:
                # st.audio_input returns an UploadedFile, read its bytes
                audio_bytes = audio_input.read()
                # Reset the UploadedFile pointer for potential reuse
                audio_input.seek(0)
                st.audio(audio_bytes, format="audio/wav")
                # Create a BytesIO object from the bytes
                audio_file = BytesIO(audio_bytes)
                audio_file.name = "recording.wav"
                audio_file.type = "audio/wav"
                # Reset BytesIO pointer to beginning
                audio_file.seek(0)
        else:
            audio_file = st.file_uploader(
                "Upload Audio File",
                type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
                help="Supported formats: WAV, MP3, M4A, FLAC, OGG"
            )
            if audio_file:
                st.audio(audio_file, format=audio_file.type)
        
        if audio_file:
            if st.button("🎤 Process Voice Query", type="primary", use_container_width=True):
                start_time = time.time()
                with st.spinner("Processing audio and generating answer..."):
                    result = voice_query(audio_file)
                    if result:
                        elapsed_time = time.time() - start_time
                        st.success(f"✅ Voice query completed! (Time: {elapsed_time:.2f}s)")
                        
                        # Save to history
                        if "query_history" not in st.session_state:
                            st.session_state.query_history = []
                        st.session_state.query_history.append({
                            "type": "Voice Query",
                            "query": result.get("transcription", ""),
                            "transcription": result.get("transcription", ""),
                            "answer": result.get("answer", ""),
                            "sources": result.get("sources", []),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.markdown("### 🎯 Transcription")
                        transcription_text = result.get("transcription", "No transcription")
                        with st.expander("📄 Transcription", expanded=True):
                            st.write(transcription_text)
                        
                        st.markdown("### 📋 Answer")
                        answer_text = result.get("answer", "No answer")
                        with st.expander("📄 Answer", expanded=True):
                            st.write(answer_text)
                        
                        sources = result.get("sources", [])
                        if sources:
                            st.markdown(f"### 📚 Sources ({result.get('num_sources', 0)})")
                            
                            # Source score visualization
                            if len(sources) > 0:
                                score_data = {f"Source {i+1}": [s.get('score', 0)] for i, s in enumerate(sources)}
                                st.bar_chart(score_data)
                            
                            for i, source in enumerate(sources, 1):
                                with st.expander(f"📄 {i}. {source.get('title', 'Unknown')} (Score: {source.get('score', 0):.3f})"):
                                    st.write(f"**Campaign ID:** {source.get('campaign_id', 'N/A')}")
                                    st.write(f"**Score:** {source.get('score', 0):.4f}")
    
    with tab3:
        st.header("Transcribe Audio")
        st.markdown("Record audio or upload an audio file to get transcription only (no RAG query).")
        
        st.info("💡 **Tip:** For best transcription quality, speak clearly in a quiet environment. Uploaded files typically produce better results than browser recordings.")
        
        option_transcribe = st.radio(
            "Choose input method:",
            ["🎤 Record Audio", "📁 Upload File"],
            horizontal=True,
            key="transcribe_option"
        )
        
        audio_file_transcribe = None
        
        if option_transcribe == "🎤 Record Audio":
            audio_input_transcribe = st.audio_input("Record your audio", key="transcribe_audio_input")
            if audio_input_transcribe:
                # st.audio_input returns an UploadedFile, read its bytes
                audio_bytes_transcribe = audio_input_transcribe.read()
                # Reset the UploadedFile pointer for potential reuse
                audio_input_transcribe.seek(0)
                st.audio(audio_bytes_transcribe, format="audio/wav")
                # Create a BytesIO object from the bytes
                audio_file_transcribe = BytesIO(audio_bytes_transcribe)
                audio_file_transcribe.name = "recording.wav"
                audio_file_transcribe.type = "audio/wav"
                # Reset BytesIO pointer to beginning
                audio_file_transcribe.seek(0)
        else:
            audio_file_transcribe = st.file_uploader(
                "Upload Audio File",
                type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
                key="transcribe_uploader",
                help="Supported formats: WAV, MP3, M4A, FLAC, OGG"
            )
            if audio_file_transcribe:
                st.audio(audio_file_transcribe, format=audio_file_transcribe.type)
        
        if audio_file_transcribe:
            if st.button("📝 Transcribe", type="primary", use_container_width=True):
                with st.spinner("Transcribing audio..."):
                    result = transcribe_audio(audio_file_transcribe)
                    if result:
                        st.success("✅ Transcription completed!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Language", result.get("language", "Unknown").upper())
                        with col2:
                            st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                        
                        st.markdown("### 📝 Transcription Result")
                        transcription_result = result.get("text", "No transcription")
                        with st.expander("📄 Transcription", expanded=True):
                            st.write(transcription_result)
                        
                        # Download button
                        st.download_button(
                            "💾 Download Transcription",
                            transcription_result,
                            file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key="download_transcription",
                            use_container_width=True
                        )
    
    with tab4:
        st.header("Scrape & Index Campaigns")
        st.markdown("Scrape campaigns from CEPTETEB website and index them for RAG queries.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🕷️ Scrape Campaigns", use_container_width=True):
                with st.spinner("Scraping campaigns (this may take a few minutes)..."):
                    result = scrape_campaigns()
                    if result:
                        st.success("✅ Scraping completed!")
                        st.json(result)
        
        with col2:
            if st.button("📚 Index Campaigns", use_container_width=True, type="primary"):
                with st.spinner("Scraping and indexing campaigns (this may take several minutes)..."):
                    result = index_campaigns()
                    if result:
                        st.success("✅ Indexing completed!")
                        st.json(result)
        
        st.info("💡 **Tip:** Indexing automatically scrapes campaigns first to ensure latest data.")
    
    with tab5:
        st.header("Statistics & Information")
        
        health = check_health()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = health.get("status", "unknown")
            if status == "healthy":
                st.metric("System Status", "✅ Healthy", delta="Operational")
            else:
                st.metric("System Status", "❌ Degraded", delta="Issues Detected", delta_color="inverse")
        
        with col2:
            stt_status = health.get("stt_service", "unknown")
            if stt_status == "healthy":
                st.metric("STT Service", "✅ Online", delta="Ready")
            else:
                st.metric("STT Service", "❌ Offline", delta="Unavailable", delta_color="inverse")
        
        with col3:
            rag_status = health.get("rag_service", "unknown")
            if rag_status == "healthy":
                st.metric("RAG Service", "✅ Online", delta="Ready")
            else:
                st.metric("RAG Service", "❌ Offline", delta="Unavailable", delta_color="inverse")
        
        st.divider()
        
        st.markdown("### 📖 API Endpoints")
        
        endpoints = {
            "Text Query": "POST /api/v1/text-query",
            "Voice Query": "POST /api/v1/voice-query",
            "Transcribe": "POST /api/v1/transcribe",
            "Scrape": "POST /api/v1/scrape",
            "Index": "POST /api/v1/index",
            "Health": "GET /health"
        }
        
        for name, endpoint in endpoints.items():
            st.code(f"{endpoint}", language=None)
        
        st.divider()
        
        st.markdown("### 🔗 Quick Links")
        st.markdown("""
        - **Gateway:** http://localhost:8000
        - **STT Service:** http://localhost:8001
        - **RAG Service:** http://localhost:8002
        - **API Docs:** http://localhost:8000/docs
        """)
    
    with tab6:
        st.header("Query History")
        st.markdown("View your recent queries and results.")
        
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.query_history = []
            st.success("History cleared!")
            st.rerun()
        
        if st.session_state.query_history:
            for idx, entry in enumerate(reversed(st.session_state.query_history[-20:]), 1):
                with st.expander(f"📝 Query #{len(st.session_state.query_history) - idx + 1}: {entry.get('query', 'Unknown')[:50]}... ({entry.get('timestamp', 'Unknown')})"):
                    st.write(f"**Type:** {entry.get('type', 'Unknown')}")
                    st.write(f"**Query:** {entry.get('query', 'N/A')}")
                    if entry.get('answer'):
                        st.write(f"**Answer:** {entry.get('answer', 'N/A')[:200]}...")
                    if entry.get('transcription'):
                        st.write(f"**Transcription:** {entry.get('transcription', 'N/A')}")
                    if entry.get('sources'):
                        st.write(f"**Sources:** {len(entry.get('sources', []))} found")
        else:
            st.info("No query history yet. Start asking questions to see them here!")

if __name__ == "__main__":
    main()

