# from django.urls import path
# from chatbot import views  # import from the chatbot app

# urlpatterns = [
#     path("chatbot_response/", views.chatbot_response, name="chatbot_response"),
#     path("chat/", views.chat_page, name="chat_page"),
# ]

from django.urls import path
from .views import chat_page, chatbot_response, signup_view, login_view, logout_view
from . import views

urlpatterns = [
    path("upload/", views.upload_document, name="upload_document"),
    path('', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('chat/', chat_page, name='chat_page'),
    path('chatbot_response/', chatbot_response, name='chatbot_response'),
]

