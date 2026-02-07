# chatbot_core.py

def get_chatbot_response(user_input: str) -> str:
    """
    Dummy chatbot logic for testing.
    Replace this with your RAG / model response logic.
    """
    # Example simple response logic
    user_input = user_input.lower()
    if "law" in user_input or "legal" in user_input:
        return "This is a legal reference chatbot. How can I assist with your query?"
    elif "hello" in user_input:
        return "Hello! How are you today?"
    else:
        return "I'm here to help! Please provide more details about your question."
