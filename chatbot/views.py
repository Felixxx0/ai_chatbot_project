import os
import json
from dotenv import load_dotenv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django import forms

from .models import ChatThread, ChatMessage, UploadedDocument
import google.generativeai as genai

# ------------------------------
# Third-party libraries for text extraction
# ------------------------------
import pdfplumber
from docx import Document
import extract_msg

# ------------------------------
# Gemini API Setup
# ------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    print("✅ Gemini API Key loaded successfully")
else:
    print("❌ GEMINI_API_KEY not found in .env file!")

model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------------------
# Document Upload Form
# ------------------------------
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ["file"]

# ------------------------------
# Utility: Extract text from files
# ------------------------------
def extract_text_from_file(file):
    """
    Extract text from uploaded file (PDF, DOCX, TXT, MSG)
    """
    filename = file.name.lower()
    
    try:
        # PDF
        if filename.endswith(".pdf"):
            text = ""
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        
        # DOCX
        elif filename.endswith(".docx"):
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
        
        # MSG (email)
        elif filename.endswith(".msg"):
            # Save temporary file for extract_msg
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            msg = extract_msg.Message(tmp_path)
            return msg.body or ""
        
        # TXT or other simple text files
        else:
            return file.read().decode("utf-8").strip()
    
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return ""

# ------------------------------    
# Views
# ------------------------------
@login_required
def upload_document(request):
    if request.method == "POST" and request.FILES.get("file"):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.name = request.FILES["file"].name
            doc.content = extract_text_from_file(request.FILES["file"])
            doc.save()
            return redirect("chat_page")
    else:
        form = DocumentUploadForm()
    return render(request, "chatbot/upload.html", {"form": form})


@login_required
def chat_page(request):
    history = ChatMessage.objects.filter(thread__user=request.user).order_by("timestamp")
    docs = UploadedDocument.objects.filter(user=request.user).order_by("-uploaded_at")
    return render(request, "chatbot/chat.html", {"history": history, "docs": docs})

# ------------------------------
# Chatbot Response API
# ------------------------------
@csrf_exempt
@login_required
@csrf_exempt
@login_required
def chatbot_response(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        thread_id = data.get("thread_id")

        # ------------------------------
        # Select or create thread
        # ------------------------------
        if thread_id:
            thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        else:
            thread = ChatThread.objects.create(
                user=request.user,
                title=user_message[:30] if user_message else "New Chat"
            )

        # ------------------------------
        # Save user message
        # ------------------------------
        ChatMessage.objects.create(thread=thread, sender="user", message=user_message)

        # ------------------------------
        # Build conversation history
        # ------------------------------
        past_messages = ChatMessage.objects.filter(thread=thread).order_by("timestamp")
        conversation_history = "\n".join(
            [f"{msg.sender}: {msg.message}" for msg in past_messages]
        )

        # ------------------------------
        # Include uploaded documents
        # ------------------------------
        docs = UploadedDocument.objects.filter(user=request.user).order_by("-uploaded_at")
        docs_text = "\n".join([doc.content[:2000] for doc in docs if doc.content])
        if docs_text:
            conversation_history += "\n\n📄 Document Content:\n" + docs_text

        # ------------------------------
        # Prepare prompt for Gemini API
        # ------------------------------
        prompt = f"""
You are a helpful assistant. Use the conversation history and the document content below to answer accurately.

Conversation:
{conversation_history}

Answer concisely and clearly, using the documents if relevant.
"""

        # ------------------------------
        # Call Gemini API
        # ------------------------------
        try:
            response = model.generate_content(prompt)
            bot_reply = response.text if response and response.text else "⚠️ No response"
        except Exception as e:
            bot_reply = f"❌ Gemini Error: {str(e)}"

        # ------------------------------
        # Save bot reply
        # ------------------------------
        ChatMessage.objects.create(thread=thread, sender="bot", message=bot_reply)

        # ------------------------------
        # Return conversation as JSON
        # ------------------------------
        return JsonResponse({
            "thread_id": thread.id,
            "title": thread.title,
            "messages": [
                {
                    "sender": m.sender,
                    "message": m.message,
                    "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                for m in thread.messages.all().order_by("timestamp")
            ]
        })

# ------------------------------
# Authentication Views
# ------------------------------
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'chatbot/signup.html', {'error': 'Username already exists!'})
        User.objects.create_user(username=username, email=email, password=password)
        return redirect('login')
    return render(request, 'chatbot/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('chat_page')
        else:
            return render(request, 'chatbot/login.html', {'error': 'Invalid credentials!'})
    return render(request, 'chatbot/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
