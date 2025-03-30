import json
import os
import openai
import google.generativeai as genai
import re
import importlib
import gemini
from home import botbreakdown_module, botsolver_module

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
        genai.configure(api_key="AIzaSyDQit9nAA22Lnnd66S1kfzfgq7QkYSi5Y0")
        openai.api_key = "insert key here"
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


def iterate_agents(initial_prompt, message_placeholder):
    """Run the agent interaction and display results in the given placeholder"""
    chat_history_a = []
    chat_history_b = []
    agent_a_response = None
    agent_b_response = None
    problem = initial_prompt
    iteration_count = 0
    
    # Results to display - clean, focused format
    conversation_html = []
    
    while True:
        iteration_count += 1
        
        # Agent A's turn
        success_a, agent_a_response = gemini.get_questioner(problem, chat_history_a)
        if not success_a:
            conversation_html.append(f'<div class="agent-a"><div class="agent-label">Agent A Error:</div>{agent_a_response["response"]}</div>')
            break

        # Display Agent A's question/prompt
        conversation_html.append(f'<div class="agent-a"><div class="agent-label">Question {iteration_count}:</div>{agent_a_response["response"]}</div>')
        
        # Add the response to the chat history
        chat_history_a.append({"parts": [{"text": problem}], "role": "user"})
        chat_history_a.append({"parts": [{"text": json.dumps(agent_a_response)}], "role": "model"})

        # Update the display
        message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)

        # Check if the response contains a solution pattern
        is_solution = agent_a_response.get("isSolution", False)
        
        if is_solution:
            conversation_html.append(f'<div class="solution"><div class="agent-label">Solution:</div>{agent_a_response["response"]}</div>')
            message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
            break

        # Agent B's turn
        success_b, agent_b_response = get_answerer(agent_a_response["response"], chat_history_b)
        if not success_b:
            conversation_html.append(f'<div class="agent-b"><div class="agent-label">Agent B Error:</div>{agent_b_response["response"]}</div>')
            message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
            break

        # Display Agent B's answer
        conversation_html.append(f'<div class="agent-b"><div class="agent-label">Answer {iteration_count}:</div>{agent_b_response["response"]}</div>')
        
        # Update chat history
        chat_history_b.append({"parts": [{"text": agent_a_response["response"]}], "role": "user"})
        chat_history_b.append({"parts": [{"text": json.dumps(agent_b_response)}], "role": "model"})
        problem = agent_b_response["response"]

        # Update the display
        message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)

        # Check for solution pattern in Agent B's response
        if "x =" in problem or "x=" in problem:
            final_prompt = f"Based on Agent B's response: '{problem}', please confirm if this is the correct solution to the original problem. If it is, set 'isSolution' to true in your response."
            success_a, agent_a_response = gemini.get_questioner(final_prompt, chat_history_a)
            if success_a and agent_a_response.get("isSolution", False):
                conversation_html.append(f'<div class="solution"><div class="agent-label">Solution:</div>{agent_a_response["response"]}</div>')
                message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
                break

        if iteration_count >= 5:  # safety measure
            final_prompt = f"You've reached the maximum number of iterations. Based on all the steps so far, please synthesize a final solution to the original problem. Include 'isSolution': true in your response."
            success_a, agent_a_response = gemini.get_questioner(final_prompt, chat_history_a)
            if success_a:
                conversation_html.append(f'<div class="solution"><div class="agent-label">Final Solution:</div>{agent_a_response["response"]}</div>')
            message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
            break
    
    # Return the HTML content and final solution
    return "\n".join(conversation_html), agent_a_response["response"] if agent_a_response else "No solution found."