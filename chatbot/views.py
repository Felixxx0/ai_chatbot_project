import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import google.generativeai as genai
from .models import ChatThread, ChatMessage, UploadedDocument
from django import forms

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


class DocumentUploadForm(forms.ModelForm):

    class Meta:
        model = UploadedDocument
        fields = ["file"]


# ------------------------------
# Chat Page View
# ------------------------------
@login_required
def upload_document(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            return redirect("chat_page")
    else:
        form = DocumentUploadForm()
    return render(request, "chatbot/upload.html", {"form": form})


def chat_page(request):
    history = ChatMessage.objects.filter(
        thread__user=request.user).order_by("timestamp")
    docs = UploadedDocument.objects.filter(
        user=request.user).order_by("-uploaded_at")
    return render(request, "chatbot/chat.html", {
        "history": history,
        "docs": docs
    })


# ------------------------------
# Chatbot Response API
# ------------------------------
@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        thread_id = data.get("thread_id")

        # ✅ Step 1: Select or create thread
        if thread_id:
            thread = get_object_or_404(ChatThread,
                                       id=thread_id,
                                       user=request.user)
        else:
            thread = ChatThread.objects.create(
                user=request.user,
                title=user_message[:30] if user_message else "New Chat")

        # ✅ Step 2: Save user message
        ChatMessage.objects.create(thread=thread,
                                   sender="user",
                                   message=user_message)

        # ✅ Step 3: Call Gemini API
        try:
            response = model.generate_content(user_message)
            bot_reply = response.text if response and response.text else "⚠️ No response from Gemini"
        except Exception as e:
            bot_reply = f"❌ Gemini Error: {str(e)}"

        # ✅ Step 4: Save bot reply
        ChatMessage.objects.create(thread=thread,
                                   sender="bot",
                                   message=bot_reply)

        # ✅ Step 5: Return conversation
        return JsonResponse({
            "thread_id":
            thread.id,
            "title":
            thread.title,
            "messages": [{
                "sender": m.sender,
                "message": m.message,
                "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for m in thread.messages.all().order_by("timestamp")]
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
            return render(request, 'chatbot/signup.html',
                          {'error': 'Username already exists!'})
        User.objects.create_user(username=username,
                                 email=email,
                                 password=password)
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
            return render(request, 'chatbot/login.html',
                          {'error': 'Invalid credentials!'})
    return render(request, 'chatbot/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
