import json
import os
import google.generativeai as genai
import re
import importlib
import gemini
import chatgpt
from dotenv import load_dotenv


# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")


get_questioner = gemini.get_questioner
get_answerer = gemini.get_answerer

#model if gemini, system if gpt 
role = "model"

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
        
        # Agent A's turn - now use the local get_questioner function
        success_a, agent_a_response = get_questioner(problem, chat_history_a)
        if not success_a:
            conversation_html.append(f'<div class="agent-a"><div class="agent-label">Agent A Error:</div>{agent_a_response["response"]}</div>')
            break

        # Display Agent A's question/prompt
        conversation_html.append(f'<div class="agent-a"><div class="agent-label">Question {iteration_count}:</div>{agent_a_response["response"]}</div>')
        
        # Add the response to the chat history
        chat_history_a.append({"parts": [{"text": problem}], "role": "user"})
        chat_history_a.append({"parts": [{"text": json.dumps(agent_a_response)}], "role": role})

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
            success_a, agent_a_response = get_questioner(final_prompt, chat_history_a)
            if success_a and agent_a_response.get("isSolution", False):
                conversation_html.append(f'<div class="solution"><div class="agent-label">Solution:</div>{agent_a_response["response"]}</div>')
                message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
                break

        if iteration_count >= 7:  # safety measure
            final_prompt = f"You've reached the maximum number of iterations. Based on all the steps so far, please synthesize a final solution to the original problem. Include 'isSolution': true in your response."
            success_a, agent_a_response = get_questioner(final_prompt, chat_history_a)
            if success_a:
                conversation_html.append(f'<div class="solution"><div class="agent-label">Final Solution:</div>{agent_a_response["response"]}</div>')
            message_placeholder.markdown("\n".join(conversation_html), unsafe_allow_html=True)
            break
    
    # Return the HTML content and final solution
    return "\n".join(conversation_html), agent_a_response["response"] if agent_a_response else "No solution found."