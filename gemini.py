import json
import os
import openai
import google.generativeai as genai
import re
import importlib
import gemini
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
agent_a_rule = """
You are Agent A. Your role is to generate sub-prompts in a 'chain of thought' manner to break down a complex problem for Agent B to solve.
- Generate one sub-prompt at a time and do not solve the original problem yourself.
- Evaluate Agent B's response for correctness, relevance, and safety. If unsatisfied, ask for a different approach.
- Follow this JSON format for all responses:
{"response": x, "isSolution": y}
- 'response': the next sub-prompt (or final solution).
- 'isSolution': true only when a final solution is reached.
- Do not generate more than 5 sub-prompts. If the limit is reached, synthesize a solution using prior responses instead of prompting further.
"""

agent_b_rule = """
You are Agent B. Your role is to respond thoughtfully and accurately to each sub-prompt from Agent A.
- Provide clear, concise, and relevant answers based on the given sub-prompt.
- If a sub-prompt is unclear, request clarification before responding.
- Ensure responses are logical, correct, and aligned with the original problem.
- Follow this JSON format for all responses:
{"response": x}
where 'x' is your answer to the given sub-prompt.
- If Agent A asks for a different approach, refine your response accordingly and try again.
"""


# First issue: the gemini import and function references need to be consistent
# Either import all functions from gemini module or define all functions locally

def clean_json_string(json_str):
    """Clean and extract proper JSON from the response string"""
    # Remove any markdown code block formatting
    json_str = re.sub(r'```json\s*|\s*```', '', json_str).strip()
    
    # Try to find and extract a JSON object
    match = re.search(r'\{.*\}', json_str, re.DOTALL)
    if match:
        return match.group(0)
    return json_str

def configure_api():
    try:
        genai.configure(api_key=api_key)
        return True, None
    except Exception as e:
        return False, str(e)
    
def get_answerer(prompt, chat_history=None):
    """Function for Agent B to respond to prompts"""
    api_configured, error = configure_api()
    if not api_configured:
        return False, {"response": f"Gemini API is not configured properly. Error: {error}"}

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')

        if chat_history:
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(f"{agent_b_rule}\n{prompt}")
        else:
            response = model.generate_content(f"{agent_b_rule}\n{prompt}")

        text_response = response.text
        # Clean the response
        clean_response = clean_json_string(text_response)
        
        try:
            structured_response = json.loads(clean_response)
        except json.JSONDecodeError:
            structured_response = {"response": text_response}

        return True, structured_response
    except Exception as e:
        return False, {"response": f"Error: {str(e)}"}
    
def get_questioner(prompt, chat_history=None):
    """Function for Agent A to generate prompts"""
    api_configured, error = configure_api()
    if not api_configured:
        return False, {"response": f"Gemini API is not configured properly. Error: {error}", "isSolution": False}

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Add explicit instructions to ensure correct JSON format
        reinforced_prompt = f"{prompt}\n\nIMPORTANT: Your response MUST include both 'response' and 'isSolution' fields in valid JSON format. Set 'isSolution' to true if this is the final solution."

        if chat_history:
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(f"{agent_a_rule}\n{reinforced_prompt}")
        else:
            response = model.generate_content(f"{agent_a_rule}\n{reinforced_prompt}")

        text_response = response.text
        # Clean the response
        clean_response = clean_json_string(text_response)
        
        try:
            structured_response = json.loads(clean_response)
            
            # Check if the response contains an answer pattern that suggests it's a solution
            answer_pattern = re.compile(r'x\s*=\s*\d+')
            response_text = structured_response.get("response", "")
            
            # Determine if it's a solution based on content or explicit flag
            is_solution = structured_response.get("isSolution", False)
            
            # If isSolution isn't set but the response looks like a solution, set it
            if not is_solution and answer_pattern.search(response_text):
                structured_response["isSolution"] = True
                is_solution = True
            
            # Make sure the isSolution field exists
            if "isSolution" not in structured_response:
                structured_response["isSolution"] = is_solution
                
        except json.JSONDecodeError:
            structured_response = {"response": text_response, "isSolution": False}

        return True, structured_response
    except Exception as e:
        return False, {"response": f"Error: {str(e)}", "isSolution": False}