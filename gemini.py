import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBq0Ejk9DOBdFIi7PkquqGCagR2HOGXeD4")  # Replace with your actual API key if not using .env

# Configure the API
try:
    genai.configure(api_key=API_KEY)
    API_CONFIGURED = True
except Exception as e:
    API_CONFIGURED = False
    API_ERROR = str(e)

def is_configured():
    """Check if the API is properly configured."""
    return API_CONFIGURED

def get_configuration_error():
    """Return the configuration error if any."""
    if not API_CONFIGURED:
        return API_ERROR
    return None

def get_response(prompt, chat_history=None):
    """Get a response from the Gemini model."""
    if not API_CONFIGURED:
        return False, "Gemini API is not configured properly. Please check your API key."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        if chat_history:
            # Create a chat session using previous history
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(prompt)
        else:
            # Simple content generation
            response = model.generate_content(prompt)
        
        return True, response.text
    except Exception as e:
        return False, f"Error: {str(e)}"