import streamlit as st
import gemini

# Page configuration
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
        margin-bottom: 0px; /* Reduced to 0px from 16px */
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
        margin-top: 0px; /* Added to remove top spacing */
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "breakdown_bot" not in st.session_state:
    st.session_state.breakdown_bot = "ChatGPT"
if "solver_bot" not in st.session_state:
    st.session_state.solver_bot = "Claude"

# Available bots
available_bots = ["ChatGPT", "Claude", "Gemini"]

# Sidebar for bot selection and about info
with st.sidebar:
    st.markdown("## ECHO")
    st.markdown("### Chain of Thought")
    
    # Replace checkboxes with two dropdown selectors
    st.markdown("#### Select Bots:")
    
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
    
    # About section (minimized)
    with st.expander("About", expanded=False):
        st.markdown("""
        **ECHO** creates a chain of thought by passing conversations through two steps:
        
        1. The breakdown bot analyzes your question
        2. The solver bot provides the final solution
        
        You can use the same bot for both roles or combine different bots' strengths.
        """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main content area with minimal professional dark theme
chain_description = f"{st.session_state.breakdown_bot} → {st.session_state.solver_bot}"
st.markdown(f"<h2 style='text-align: center; margin-bottom: 6px;'>ECHO</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #90cdf4; margin-bottom: 20px;'>{chain_description}</p>", unsafe_allow_html=True)

# API configuration check
if not gemini.is_configured():
    error = gemini.get_configuration_error()
    st.error(f"API is not configured properly. Error: {error}")
    st.info("Please set your API key in the configuration settings.")
    st.stop()

# Create a container for chat messages
with st.container():
    # Display chat messages with minimal styling
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=None):
            st.write(message["content"])

# Add a small spacer
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Chat input below the conversation
if prompt := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with the selected bots
    with st.chat_message("assistant"):
        with st.spinner(f"Processing with {st.session_state.breakdown_bot} → {st.session_state.solver_bot}..."):
            # Convert session state messages to format expected by API
            chat_history = [
                {"role": "user" if msg["role"] == "user" else "model", 
                 "parts": [msg["content"]]}
                for msg in st.session_state.messages[:-1]  # Exclude the current message
            ]
            
            
            # # Breakdown bot processing
            success, breakdownlst = gemini.get_response(
                 f"Break down this question into multiple subproblems and split each with a comma : {prompt}",
                 chat_history if chat_history else None
             )
            breakdownlst = breakdownlst.split(',')
            conversation = []
            
            # for i in range(len(breakdownlst)):
            #     success, answer = gemini.get_response(f" solve this subproblem: {breakdownlst[i]}", conversation)
            #     success, check = gemini.get_response(f" doublecheck if this is proper solution to previous subproblem: {answer}", conversation)
            #     conversation += [(answer , check)]

            
            # # Solver bot processing
            # success, final_response = gemini.get_response(
            #     f"Based on this breakdown: '{breakdown_response}', provide a comprehensive answer to the original question: '{prompt}'",
            #     chat_history if chat_history else None
            # )
            
            # # Display the final response
            final_response = breakdownlst

            print(breakdownlst)
            print('/n', type(breakdownlst))
            print("history:", chat_history)
            final_response = '\n'.join(breakdownlst)
            st.write(final_response)
    
    # Add final assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": final_response
    })
    
    # Force a rerun to update the UI with the new messages and reset the input field
    st.rerun()