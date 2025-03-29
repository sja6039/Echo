import streamlit as st
import gemini

# Page configuration
st.set_page_config(page_title="ECHO - Chain of Thought Chatbot", page_icon="🤖", layout="centered")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Application header
st.title("ECHO")
st.subheader("💬 Chain of Thought Chatbot")
st.caption("Chat multiple AI models")

# Check if API is configured
if not gemini.is_configured():
    error = gemini.get_configuration_error()
    st.error(f"Gemini API is not configured properly. Error: {error}")
    st.info("Please set your API key in the gemini.py file or as an environment variable named 'GEMINI_API_KEY'.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Convert session state messages to format Gemini expects
            chat_history = [
                {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
                for msg in st.session_state.messages[:-1]  # Exclude the current message
            ]
            
            # Get response from Gemini
            success, response = gemini.get_response(prompt, chat_history if chat_history else None)
            st.write(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with additional options
with st.sidebar:
    st.header("About")
    st.markdown("""
    This chatbot uses Google's Gemini AI model to generate responses to your questions.
    
    To get started:
    1. Make sure your Gemini API key is set in gemini.py or as an environment variable
    2. Ask any question in the chat input
    3. The chatbot will respond with an answer
    """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()