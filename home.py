import os
import streamlit as st
import google.generativeai as genai
import collaberator
# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="ECHO",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Custom CSS for minimal professional dark theme with fixed spacing and chat improvements
st.markdown("""
<style>
    .main {
        padding: 2rem 3rem;
        color: #e0e0e0;
    }
    .stApp {
        background-color: #121212;
    }
    .chat-container {
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin-bottom: 0px;
    }
    .sidebar .block-container {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 12px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #2c5282;
        color: white;
    }
    .stButton>button:hover {
        background-color: #3182ce;
    }
    .stExpander {
        background-color: #1e1e1e;
        border-radius: 8px;
    }
    .stTextInput>div>div>input {
        background-color: #2d3748;
        color: #e0e0e0;
        border-radius: 8px;
    }
    .stChatInputContainer {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 4px;
        margin-top: 0px;
        position: relative !important;
        top: auto !important;
        bottom: auto !important;
        left: auto !important;
        right: auto !important;
        margin-top: 20px !important;
        order: 999 !important;
    }
    .stChatInput>div>div>textarea {
        background-color: #2d3748;
        color: #e0e0e0;
        border-radius: 15px;
    }
    .stSelectbox>div>div {
        background-color: #2d3748;
        color: #e0e0e0;
        border-radius: 8px;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: #e0e0e0;
    }
    .st-emotion-cache-1wmy9hl {
        background-color: #2d3748;
        color: #e0e0e0;
    }
    .st-emotion-cache-1inwz65 {
        color: #e0e0e0;
    }
    .st-emotion-cache-16txtl3 {
        background-color: #2d3748;
    }
    .st-emotion-cache-lrlib {
        fill: #e0e0e0;
    }

    .stChatMessageContent, .stChatMessage {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Make the chat container use flex column layout */
    .main .block-container {
        padding-bottom: 0;
        display: flex !important;
        flex-direction: column !important;
    }

    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Fix for avatar clipping and centering */
    .stChatMessage {
        padding-top: 16px !important;
        padding-bottom: 16px !important;
    }
    
    /* Adjust avatar positioning */
    .stChatMessageAvatar {
        margin-top: 6px !important;
    }
    
    /* Ensure proper spacing for avatar container */
    .st-emotion-cache-eczf16 {
        padding-top: 8px !important;
        padding-bottom: 8px !important;
    }
    
    /* Give more space for the avatar container */
    .st-emotion-cache-7ym5gk {
        min-width: 42px !important;
        margin-right: 8px !important;
    }

    /* Agent conversation styling */
    .agent-a {
        background-color: rgba(100, 149, 237, 0.15);
        border-left: 3px solid cornflowerblue;
        padding: 10px 15px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .agent-b {
        background-color: rgba(144, 238, 144, 0.15);
        border-left: 3px solid lightgreen;
        padding: 10px 15px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .agent-label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .solution {
        background-color: rgba(255, 215, 0, 0.15);
        border-left: 3px solid gold;
        padding: 10px 15px;
        margin: 12px 0;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "breakdown_bot" not in st.session_state:
    st.session_state.breakdown_bot = "Gemini"
if "solver_bot" not in st.session_state:
    st.session_state.solver_bot = "Gemini"

# Sidebar for configuration
with st.sidebar:
    st.markdown("## ECHO")
    st.markdown("### Chain of Thought")
        
    st.markdown("#### Select Bots:")
    
    available_bots = ["ChatGPT", "Gemini"]

    # Dropdown for breakdown bot
    st.session_state.breakdown_bot = st.selectbox(
        "Select bot to break down the question:",
        available_bots,
        index=available_bots.index(st.session_state.breakdown_bot) if st.session_state.breakdown_bot in available_bots else 0
    )
    
    # Dropdown for solver bot
    st.session_state.solver_bot = st.selectbox(
        "Select bot to provide the solution:",
        available_bots,
        index=available_bots.index(st.session_state.solver_bot) if st.session_state.solver_bot in available_bots else 1
    )
    
    st.divider()

    # About section
    with st.expander("About", expanded=True):
        st.markdown("""
        **ECHO** creates a chain of thought by passing conversations through three steps:
        
        1. The breakdown bot analyzes your question creating several subequestions to then send to the solver bot.
        2. The solver bot provides then solves each subproblem given from the breakdown bot, then returns the solution to the breakdown bot.
        3. The original breakdown bot then verifies the solution and gives the solution back to the user.
        
        You can use the same bot for both roles or combine different bots' strengths.
        """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main content area
st.markdown(f"<h2 style='text-align: center; justify-content: center; margin-bottom: 6px;'>ECHO</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #90cdf4; margin-bottom: 20px;'>Chain of Thought Problem Solver</p>", unsafe_allow_html=True)

# Test the API configuration
genai.configure(api_key="AIzaSyDQit9nAA22Lnnd66S1kfzfgq7QkYSi5Y0")


# Display chat messages
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=None):
            if message["role"] == "assistant" and "<div class=" in message["content"]:
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

# Add a small spacer
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with the agents
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Processing your request...")
        
        # Run the agent interaction with live updates to the placeholder
        conversation_html, solution = collaberator.iterate_agents(prompt, message_placeholder)
        
        # Display final conversation
        message_placeholder.markdown(conversation_html, unsafe_allow_html=True)
    
    # Add final assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": conversation_html
    })