import os
import google.generativeai as genai

def generate_text_with_gemini(project_data: dict) -> str:
    """
    Generates text using the Google Gemini API, prioritizing Core Narrative Brief,
    then structured story elements, then legacy key messages.
    Incorporates specified tone and style.
    
    :param project_data: A dictionary containing project details.
    :return: Generated text from Gemini or an error message string.
    """
    GOOGLE_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_GEMINI_API_KEY environment variable not set.")
        return "ERROR: GOOGLE_GEMINI_API_KEY not configured. Cannot connect to AI service."

    project_name = project_data.get('project_name', 'the company/project')
    primary_audience = project_data.get('primary_audience_input', 'the target audience')
    selected_tone = project_data.get('tone', 'neutral')
    selected_style = project_data.get('style', 'standard_pr')
    content_prompt_part = ""
    prompt_strategy_used = "none_available"

    if project_data.get('core_narrative_brief'):
        content_prompt_part = f"Base the press release on the following 'Core Narrative Brief':\n{project_data['core_narrative_brief']}\n\nAdditional context if available:\nProject Name: {project_name}\nMain Takeaway (if not fully in brief): {project_data.get('main_takeaway_input', 'N/A')}\nAudience Benefit (if not fully in brief): {project_data.get('audience_benefit_input', 'N/A')}\nDifferentiator (if not fully in brief): {project_data.get('differentiator_input', 'N/A')}"
        prompt_strategy_used = "core_narrative_brief"
    elif project_data.get('main_takeaway_input') and project_data.get('primary_audience_input'):
        content_prompt_part = f"Base the press release on the following key elements:\nProject Name: {project_name}\nMain Takeaway: {project_data.get('main_takeaway_input', 'Not specified')}\nPrimary Audience for this News: {primary_audience}\nWhy This Audience Should Care (Benefit/Impact): {project_data.get('audience_benefit_input', 'Not specified')}\nKey Differentiator/Uniqueness: {project_data.get('differentiator_input', 'Not specified')}\nDesired Outcome of the Press Release: {project_data.get('desired_outcome_input', 'Not specified')}"
        prompt_strategy_used = "story_elements"
    elif project_data.get('key_messages') or project_data.get('target_audience_keywords'):
        content_prompt_part = f"Base the press release on the following for a project named '{project_name}':\nKey Messages: {project_data.get('key_messages', 'No specific key messages provided.')}\nTarget Audience Keywords: {project_data.get('target_audience_keywords', 'General audience.')}"
        prompt_strategy_used = "legacy_fields"
    else:
        return "ERROR: Insufficient project data to generate a press release prompt."

    prompt = f"Generate a comprehensive press release. The press release should be well-structured and suitable for {primary_audience}. It must include a compelling headline, an introductory paragraph, supporting details and quotes (you may need to invent plausible quotes based on the provided information if none are explicitly given), a boilerplate about {project_name}, and contact information (use placeholders like \"[Contact Name]\" and \"[Contact Email]\").\n\n{content_prompt_part}\n\nInstruction on Tone and Style:\nAdopt a '{selected_tone}' tone for this press release.\nFormat the output as a '{selected_style}'."
    if selected_style == 'q_and_a':
        prompt += " This means the output should be structured as a series of questions and answers. The questions should anticipate what a journalist or reader might ask, and the answers should provide clear, concise information based on the provided project details."
    elif selected_style == 'story_lead':
        prompt += " This means the output should start with a compelling narrative lead, like the beginning of a feature article, drawing the reader in before presenting the core facts. The narrative should be engaging and set the scene."
    elif selected_style == 'bullet_points':
        prompt += " This means the output should primarily summarize the key information in a series of impactful bullet points, possibly with a brief introductory and concluding paragraph. Focus on conciseness and scannability."
    prompt += "\n\nBegin Press Release:"

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.0-pro')
        print(f"Attempting to generate content with Gemini for project '{project_name}'. Strategy: {prompt_strategy_used}, Tone: {selected_tone}, Style: {selected_style}")
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        print("Error: Gemini API returned an empty or unexpected response structure.")
        if response.prompt_feedback: print(f"Prompt Feedback: {response.prompt_feedback}")
        return "Error: AI service returned an empty or unexpected response."
    except Exception as e: 
        print(f"Gemini API Error (generate_text_with_gemini): {e}")
        return f"Error: Could not generate content from AI service. Details: {str(e)}"

def clarify_story_with_gemini(story_elements: dict) -> str:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_GEMINI_API_KEY environment variable not set for story clarification.")
        return "ERROR: GOOGLE_GEMINI_API_KEY not configured. Cannot connect to AI service for story clarification."
    prompt = f"Based on the following elements, synthesize a 'Core Narrative Brief' (1-2 paragraphs) that will serve as the strategic foundation for a press release. The brief should be clear, concise, and compelling.\n\nMain Takeaway: {story_elements.get('main_takeaway', 'Not specified')}\nPrimary Audience for this News: {story_elements.get('primary_audience', 'Not specified')}\nWhy This Audience Should Care (Benefit/Impact): {story_elements.get('audience_benefit', 'Not specified')}\nKey Differentiator/Uniqueness: {story_elements.get('differentiator', 'Not specified')}\nDesired Outcome of the Press Release: {story_elements.get('desired_outcome', 'Not specified')}\n\nSynthesized Core Narrative Brief:"
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.0-pro')
        print(f"Attempting to clarify story with Gemini using elements: {story_elements}")
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        print("Error: Gemini API returned an empty or unexpected response structure for story clarification.")
        if response.prompt_feedback: print(f"Prompt Feedback (clarify_story): {response.prompt_feedback}")
        return "Error: AI service returned an empty or unexpected response for story clarification."
    except Exception as e:
        print(f"Gemini API Error (clarify_story_with_gemini): {e}")
        return f"Error: Could not clarify story using AI service. Details: {str(e)}"

def refine_text_with_gemini(text_to_refine: str, refinement_type: str, original_context: str = None) -> str:
    """
    Refines a given text snippet using Google Gemini based on the refinement type.
    """
    GOOGLE_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_GEMINI_API_KEY environment variable not set for text refinement.")
        return "ERROR: GOOGLE_GEMINI_API_KEY not configured. Cannot connect to AI service for text refinement."

    context_instruction = ""
    if original_context:
        context_instruction = f"\n\nFor context, this text is part of a larger document. The surrounding content is:\n---\n{original_context[:1000]}...\n---\n" # Limit context size

    prompt = ""
    if refinement_type == 'concise':
        prompt = f"Make the following text more concise, while retaining its core meaning. If possible, suggest 2-3 options, clearly separated or numbered:\n\nText to make concise:\n'''{text_to_refine}'''{context_instruction}"
    elif refinement_type == 'alternative_phrasing':
        prompt = f"Offer 2-3 alternative phrasings for the following text, focusing on clarity and impact. Clearly separate or number the suggestions:\n\nText for alternative phrasing:\n'''{text_to_refine}'''{context_instruction}"
    elif refinement_type == 'simplify_jargon':
        prompt = f"Identify any jargon in the following text and suggest simpler alternatives or explanations. If jargon is present, list each jargon term and its suggested simplification. If no significant jargon is found, state that.\n\nText to simplify jargon in:\n'''{text_to_refine}'''{context_instruction}"
    else:
        return "ERROR: Invalid refinement type specified."

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.0-pro') # Using gemini-1.0-pro, adjust if needed
        
        print(f"Attempting text refinement with Gemini. Type: '{refinement_type}'. Snippet: '{text_to_refine[:100]}...'")
        response = model.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            refined_text = response.candidates[0].content.parts[0].text
            print("Successfully received refinement suggestion from Gemini.")
            return refined_text
        else:
            print("Error: Gemini API returned an empty or unexpected response structure for text refinement.")
            if response.prompt_feedback:
                 print(f"Prompt Feedback (refine_text): {response.prompt_feedback}")
            return "Error: AI service returned an empty or unexpected response for text refinement."

    except Exception as e:
        print(f"Gemini API Error (refine_text_with_gemini): {e}")
        return f"Error: Could not refine text using AI service. Details: {str(e)}"
