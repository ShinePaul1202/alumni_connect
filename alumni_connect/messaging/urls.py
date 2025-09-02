from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("chat/<int:user_id>/", views.chat_with_user, name="chat_with_user"),  # create/open 1:1 and redirect
    path("c/<int:pk>/", views.conversation_view, name="conversation"),         # conversation page
    path("c/<int:pk>/send/", views.send_message_ajax, name="send_message"),
    path("c/<int:pk>/fetch/", views.fetch_messages, name="fetch_messages"),
]
