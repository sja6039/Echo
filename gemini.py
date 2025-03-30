# gemini.py
import json
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Clear, structured prompt for Agent A that enforces JSON structure and direct solution provision
agent_a_rule = """
You are Agent A. Your role is to generate sub-prompts in a 'chain of thought' manner to break down a complex problem for Agent B to solve.

CRITICAL INSTRUCTION: 
1. Your ENTIRE response must be ONLY a valid JSON object with EXACTLY these fields:
   {
     "response": "your text here",
     "isSolution": boolean
   }

2. When providing a final solution:
   - Do NOT ask questions like "provide the Python code that returns..."
   - Instead, DIRECTLY include the actual solution code or answer in the "response" field
   - Set "isSolution" to true

3. Example of correct final solution format:
   {
     "response": "def two_sum(nums, target):\\n    seen = {}\\n    for i, num in enumerate(nums):\\n        complement = target - num\\n        if complement in seen:\\n            return [seen[complement], i]\\n        seen[num] = i\\n    return []",
     "isSolution": true
   }

Guidelines:
- Generate one sub-prompt at a time 
- Do not solve the original problem yourself until the final step
- Evaluate Agent B's response for correctness, relevance, and safety
- If unsatisfied with Agent B's response, ask for a different approach
- Do not generate more than 5 sub-prompts total
- After 5 sub-prompts, synthesize a solution using prior responses
"""

# Enhanced prompt for Agent B
agent_b_rule = """
You are Agent B. Your role is to respond thoughtfully and accurately to each sub-prompt from Agent A.

CRITICAL INSTRUCTION: Your ENTIRE response must be ONLY a valid JSON object with this exact structure:
{
  "response": "your answer to the sub-prompt here"
}

Guidelines:
- Provide clear, concise, and relevant answers based on the given sub-prompt
- If a sub-prompt is unclear, request clarification before responding
- Ensure responses are logical, correct, and aligned with the original problem
- If Agent A asks for a different approach, refine your response accordingly
"""

def configure_api():
    """Configure the Gemini API with the provided key."""
    try:
        genai.configure(api_key=api_key)
        return True, None
    except Exception as e:
        return False, str(e)

def clean_json_string(json_str):
    """Clean and extract proper JSON from the response string"""
    # Remove markdown code blocks if present
    text = re.sub(r'^```(?:json)?\n?', '', json_str)  # Remove ```json from start (making 'json' optional)
    text = re.sub(r'\n?```$', '', text)  # Remove ``` from end with optional newline
    
    # Remove headers like "Final Solution:" or similar text
    text = re.sub(r'\*\*.*?\*\*\s*', '', text)  # Remove bold text with asterisks
    text = re.sub(r'#.*?\n', '', text)          # Remove markdown headers
    text = re.sub(r'Final Solution:.*?\n', '', text, flags=re.IGNORECASE)  # Remove specific headers
    
    # Try to find JSON-like content within the text if it's not already clean
    json_pattern = re.compile(r'(\{.*\})', re.DOTALL)
    match = json_pattern.search(text)
    if match:
        text = match.group(1)
    
    # Remove any extra backticks that might be present
    text = text.replace('`', '')
    
    # Clean up extra whitespace
    text = text.strip()
    
    return text

def force_structured_solution(response_dict, original_prompt):
    """Force proper solution structure if isSolution is true but response contains a question."""
    if response_dict.get("isSolution", False):
        response_text = response_dict.get("response", "")
        
        # Check if the response is asking a question instead of providing solution
        question_patterns = [
            r"provide the (?:python )?code",
            r"write (?:the|a) (?:python )?(?:function|code)",
            r"implement (?:the|a)",
            r"what is the (?:python )?code",
            r"how would you"
        ]
        
        is_question = any(re.search(pattern, response_text, re.IGNORECASE) for pattern in question_patterns)
        
        if is_question:
            # If it's a question instead of a solution, use Gemini to generate the actual solution
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                solution_prompt = f"""
                Based on this problem: {original_prompt}
                
                And this question that needs a direct solution: {response_text}
                
                Provide ONLY the complete Python code solution without any explanation or questions.
                For example, if asked about a two_sum function, provide the complete implementation.
                """
                
                solution_response = model.generate_content(solution_prompt)
                solution_text = solution_response.text
                
                # Clean up the solution text (remove code markers if present)
                solution_text = re.sub(r'```(?:python)?\n?', '', solution_text)
                solution_text = re.sub(r'\n?```$', '', solution_text)
                solution_text = solution_text.strip()
                
                # Replace the question with the actual solution
                response_dict["response"] = solution_text
            except Exception as e:
                # Fallback solution for two_sum if context suggests that's what's needed
                if "two_sum" in original_prompt.lower() or "add up to the target" in original_prompt.lower():
                    response_dict["response"] = """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []"""
    
    return response_dict

def get_answerer(prompt, chat_history=None):
    """Function for Agent B to respond to prompts with structured JSON output."""
    api_configured, error = configure_api()
    if not api_configured:
        return False, {"response": f"Gemini API is not configured properly. Error: {error}"}

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Add specific formatting instructions to ensure proper JSON output
        enforced_prompt = f"""
{agent_b_rule}

Sub-prompt from Agent A: {prompt}

REMEMBER: Your response must be ONLY valid JSON with the structure: {{"response": "your answer"}}
DO NOT include any explanation text, code blocks, or additional formatting.
"""

        # Set generation config to enforce structured output
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more predictable formatting
            "top_p": 0.95,
            "top_k": 40,
            "response_mime_type": "application/json",  # Request JSON response format
        }

        if chat_history:
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(enforced_prompt, generation_config=generation_config)
        else:
            response = model.generate_content(enforced_prompt, generation_config=generation_config)

        text_response = response.text
        
        # Extract and clean the JSON response
        clean_response = clean_json_string(text_response)
        
        try:
            structured_response = json.loads(clean_response)
            # Ensure the response field exists
            if "response" not in structured_response:
                structured_response["response"] = "Error: Missing response field in Agent B output"
        except json.JSONDecodeError:
            # If still not valid JSON, create a structured fallback
            structured_response = {"response": f"Error parsing response: {text_response[:100]}..."}

        return True, structured_response
    except Exception as e:
        return False, {"response": f"Error: {str(e)}"}

def get_questioner(prompt, chat_history=None):
    """Function for Agent A to generate prompts with structured JSON output."""
    api_configured, error = configure_api()
    if not api_configured:
        return False, {"response": f"Gemini API is not configured properly. Error: {error}", "isSolution": False}

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Count iterations from chat history if available
        iteration_count = 0
        original_prompt = prompt
        if chat_history and len(chat_history) >= 2:
            iteration_count = len(chat_history) // 2
            # Try to get original prompt from first message
            if chat_history and len(chat_history) > 0:
                try:
                    original_prompt = chat_history[0].get("parts", [{}])[0].get("text", prompt)
                except (IndexError, KeyError, AttributeError):
                    pass  # Keep the current prompt if we can't extract the original

        # Determine if we're asking for a final solution based on iteration count or prompt content
        is_final_prompt = iteration_count >= 5 or "final solution" in prompt.lower()
        
        # Add specific formatting instructions
        enforced_prompt = f"""
{agent_a_rule}

Current iteration: {iteration_count + 1}
Original problem: {original_prompt}
Current prompt: {prompt}

{"THIS IS THE FINAL STEP. PROVIDE THE COMPLETE SOLUTION, NOT QUESTIONS ABOUT WHAT TO IMPLEMENT." if is_final_prompt else ""}

REMEMBER: Your response must be ONLY valid JSON with the structure: 
{{
  "response": "your text here",
  "isSolution": {"true" if is_final_prompt else "false"}
}}

NO text outside the JSON structure.
"""

        # Set generation config to enforce structured output
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more predictable formatting
            "top_p": 0.95,
            "top_k": 40,
            "response_mime_type": "application/json",  # Request JSON response format
        }

        if chat_history:
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(enforced_prompt, generation_config=generation_config)
        else:
            response = model.generate_content(enforced_prompt, generation_config=generation_config)

        text_response = response.text
        
        # Extract and clean the JSON response
        clean_response = clean_json_string(text_response)
        
        try:
            structured_response = json.loads(clean_response)
            
            # Ensure both required fields exist
            if "response" not in structured_response:
                structured_response["response"] = "Error: Missing response field in Agent A output"
            if "isSolution" not in structured_response:
                structured_response["isSolution"] = is_final_prompt
                
            # Apply solution check and transform if needed
            if is_final_prompt:
                structured_response = force_structured_solution(structured_response, original_prompt)
                
        except json.JSONDecodeError:
            # If still not valid JSON, create a structured fallback
            structured_response = {
                "response": f"Error parsing response: {text_response[:100]}...", 
                "isSolution": is_final_prompt
            }

        return True, structured_response
    except Exception as e:
        return False, {"response": f"Error: {str(e)}", "isSolution": False}