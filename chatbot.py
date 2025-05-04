import streamlit as st
from openai import OpenAI
from datetime import datetime
from functools import lru_cache
import time

# --- Configuration ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-free-key-here",  # Replace with your OpenRouter key
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Chatbot Internship Project"
    }
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stChatInput { position: fixed; bottom: 2rem; }
    .stChatMessage { padding: 12px 16px; border-radius: 18px; }
    .model-select { margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    model = st.selectbox(
        "AI Model",
        options=[
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mixtral-8x7b-instruct"
        ],
        index=0,
        key="model"
    )
    
    temperature = st.slider(
        "Creativity", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7,
        key="temp"
    )
    
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI assistant. Ask me anything!"}
    ]
if "last_request" not in st.session_state:
    st.session_state.last_request = datetime.now()

# --- Chat Display ---
st.title("💬 ChatGPT Clone")
st.caption("Built with OpenRouter's free tier for my internship project")

for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- Chat Logic with All Features ---
@lru_cache(maxsize=100)  # Cache responses
def get_ai_response(model: str, messages: tuple, temperature: float):
    """Cached API call to conserve free tier limits"""
    return client.chat.completions.create(
        model=model,
        messages=list(messages),
        temperature=temperature,
        stream=True  # Enable streaming
    )

if prompt := st.chat_input("Your message"):
    # Rate limit check
    time_since_last = (datetime.now() - st.session_state.last_request).seconds
    if time_since_last < 2:
        st.warning("⚠️ Wait 2 seconds between messages to avoid rate limits")
        st.stop()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="👤").markdown(prompt)
    
    # Generate AI response
    with st.chat_message("assistant", avatar="🤖"):
        try:
            # Convert messages to tuple for caching
            message_tuple = tuple(
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            )
            
            # Stream response
            stream = get_ai_response(
                model=model,
                messages=message_tuple,
                temperature=temperature
            )
            
            response = st.write_stream(  # Real-time typing effect
                chunk.choices[0].delta.content 
                for chunk in stream 
                if chunk.choices[0].delta.content
            )
            
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
            st.session_state.last_request = datetime.now()
            
        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            if "rate limit" in str(e).lower():
                error_msg += "\n\nTry switching models or wait 1 hour"
            st.error(error_msg)

# --- Token Counter (Demo Purpose) ---
with st.sidebar:
    st.divider()
    st.metric("💡 Pro Tip", "Cache reduces API calls")
    if len(st.session_state.messages) > 1:
        st.caption(f"Messages: {len(st.session_state.messages)-1}")