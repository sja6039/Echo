import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment

# Configure the API
# try:
#     openai.api_key = API_KEY
#     API_CONFIGURED = True
# except Exception as e:
#     API_CONFIGURED = False
#     API_ERROR = str(e)

def is_configured():
    """Check if the API is properly configured."""
    return API_CONFIGURED and openai.api_key is not None

def get_configuration_error():
    """Return the configuration error if any."""
    if not API_CONFIGURED:
        return API_ERROR
    if not openai.api_key:
        return "OpenAI API key is not set"
    return None

def get_response(prompt, chat_history=None):
    """Get a response from the ChatGPT model."""
    if not is_configured():
        return False, "ChatGPT API is not configured properly. Please check your API key."
    
    try:
        messages = []
        
        # If there's chat history, format it properly for OpenAI
        if chat_history:
            messages.extend(chat_history)
        
        # Add the current prompt as the latest user message
        messages.append({"role": "user", "content": prompt})
        
        # Call the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # You can change this to another model like "gpt-3.5-turbo"
            messages=messages
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        return True, response_text
    
    except Exception as e:
        return False, f"Error: {str(e)}"