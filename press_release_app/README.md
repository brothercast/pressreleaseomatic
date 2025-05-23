# AI-Assisted Press Release App

## Description

This project is an AI-assisted application designed to help users create and manage press releases. It leverages AI (planned integration with Google Gemini) to assist in generating press release content. This initial version provides a foundational Flask-based web application with core functionalities for project management and stubbed AI interaction.

## Current Status

This is an initial development skeleton. Key functionalities are implemented with a web UI and API, but the AI content generation is currently stubbed. The focus has been on setting up the project structure, data models, basic UI/API routes, and a placeholder for AI service integration.

## Features (Current Skeleton)

*   Flask-based backend.
*   SQLAlchemy for database interaction (SQLite).
*   Data models for Users, Projects, and Press Releases.
*   Web interface (Flask/Jinja2) for:
    *   Viewing a dashboard of projects.
    *   Creating new projects.
    *   Viewing project details.
    *   Initiating (stubbed) press release generation.
*   RESTful API endpoints for:
    *   Managing projects (`/projects`).
    *   Triggering (stubbed) press release generation.
*   Stubbed service for Google Gemini API interaction.
*   Basic Pytest setup for API testing.
*   Environment variable handling for API keys (`.env.example` provided).

## Setup Instructions

1.  **Clone the Repository (Example):**
    ```bash
    # git clone <repository_url>
    # cd press_release_app
    ```
    (Note: If you are setting this up from files provided directly, just navigate to the `press_release_app` directory.)

2.  **Create and Activate a Python Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    (On Windows: `venv\Scripts\activate`)

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your actual Google Gemini API key:
        ```
        GOOGLE_GEMINI_API_KEY="YOUR_ACTUAL_GOOGLE_GEMINI_API_KEY_HERE"
        ```
    *   The application will warn you if this key is not set, and AI features will not function correctly.

5.  **Initialize the Database:**
    The database (`press_release.db`) and its tables will be created automatically when you first run the application.

## Running the Application

1.  Ensure your virtual environment is activated and environment variables (especially `GOOGLE_GEMINI_API_KEY`) are set.
2.  From the `press_release_app` root directory, run:
    ```bash
    python app.py
    ```
3.  The application will be accessible at `http://127.0.0.1:5000/`.
4.  You can access the web UI dashboard at `http://127.0.0.1:5000/ui/dashboard`.

## Running Tests

1.  Ensure your virtual environment is activated.
2.  From the `press_release_app` root directory, run:
    ```bash
    pytest
    ```

## Future Development

*   Integrate the actual Google Gemini API for press release content generation.
*   Expand user authentication and management.
*   Develop more sophisticated frontend interactions (potentially with a JavaScript framework).
*   Implement full CRUD for all models.
*   Add features for publication identification and contact management.
*   Refine error handling and logging.
