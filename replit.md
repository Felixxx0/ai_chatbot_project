# Django Chatbot with Gemini AI

## Overview
This is a Django web application that provides a chatbot interface powered by Google's Gemini AI. Users can sign up, log in, chat with the AI, and upload documents.

## Project Architecture
- **Backend**: Django 5.2.6 web framework
- **Database**: SQLite (default Django setup)
- **AI Integration**: Google Generative AI (Gemini API)
- **Frontend**: Django templates with vanilla JavaScript
- **File Uploads**: Support for document uploads with media file handling

## Key Features
- User authentication (signup/login/logout)
- Chat interface with conversation history
- Document upload functionality
- Google Gemini AI integration for chatbot responses
- Thread-based conversation management

## Setup Status
✅ Python 3.11 installed
✅ Dependencies installed from requirements.txt
✅ Django settings configured for Replit environment
✅ Database migrations completed
✅ Development server workflow configured on port 5000
✅ Static and media file handling configured
✅ Deployment configuration set up for autoscale

## Environment Variables Required
- `SECRET_KEY`: Django secret key (auto-generated fallback available)
- `GEMINI_API_KEY`: Google Gemini API key (required for chatbot functionality)
- `DEBUG`: Set to "True" for development (default)

## Recent Changes (September 18, 2025)
- Imported project from GitHub
- Configured ALLOWED_HOSTS = ['*'] for Replit environment
- Added static and media file configuration
- Fixed chat template to properly display conversation history
- Set up deployment configuration for production
- Created Django development server workflow

## Running the Application
The application runs automatically via the configured workflow:
- Development server: `python manage.py runserver 0.0.0.0:5000`
- Access the app through the Replit webview on port 5000

## Notes
- The application currently shows a warning about missing GEMINI_API_KEY, but basic functionality works
- Users need to configure the GEMINI_API_KEY for full chatbot functionality
- Document uploads are supported and files are stored in the media directory