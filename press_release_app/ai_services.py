import os
import google.generativeai as genai
# Import other necessary google api core exceptions if known, or use a general Exception
# from google.api_core import exceptions as google_exceptions

def generate_text_with_gemini(prompt_text: str) -> str:
    """
    Generates text using the Google Gemini API.
    """
    GOOGLE_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")

    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_GEMINI_API_KEY environment variable not set.")
        return "ERROR: GOOGLE_GEMINI_API_KEY not configured. Cannot connect to AI service."

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # For text-only input, use the gemini-pro model
        model = genai.GenerativeModel('gemini-1.0-pro') # Or 'gemini-pro'
        
        # Make the API call
        print(f"Attempting to generate content with Gemini for prompt: \"{prompt_text[:100]}...\"")
        response = model.generate_content(prompt_text)
        
        # Extract the text
        if response.candidates and response.candidates[0].content.parts:
            generated_text = response.candidates[0].content.parts[0].text
            print("Successfully received content from Gemini.")
            return generated_text
        else:
            # This case might indicate an empty response or unexpected structure
            print("Error: Gemini API returned an empty or unexpected response structure.")
            if response.prompt_feedback:
                 print(f"Prompt Feedback: {response.prompt_feedback}")
            return "Error: AI service returned an empty or unexpected response."

    except Exception as e: # Catching a more general exception for now.
                           # Specific exceptions like google_exceptions.GoogleAPIError can be caught.
        print(f"Gemini API Error: {e}")
        # You might want to inspect 'e' further. If it's a specific API error,
        # e.g., related to billing, quota, or invalid API key, the message might be more specific.
        # For example, if 'e' has a 'message' attribute: error_message = e.message
        return f"Error: Could not generate content from AI service. Details: {str(e)}"
