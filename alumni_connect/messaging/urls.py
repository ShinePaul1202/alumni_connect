from django.urls import path
from . import views

# This is important for namespacing (e.g., 'messaging:inbox')
app_name = 'messaging'

urlpatterns = [
    # Page URLs
    path("inbox/", views.inbox, name="inbox"),
    path("chat/<int:user_id>/", views.chat_with_user, name="chat_with_user"),
    path("conversation/<int:pk>/", views.conversation_view, name="conversation_view"),

    # AJAX Endpoints (called by JavaScript)
    path("send/<int:pk>/", views.send_message_ajax, name="send_message_ajax"),
    path("fetch-html/<int:pk>/", views.fetch_conversation_html, name="fetch_conversation_html"),
    path("delete-message/<int:pk>/", views.delete_message_ajax, name="delete_message"),
    path("delete-bulk/", views.delete_messages_bulk_ajax, name="delete_messages_bulk_ajax"),
    path("leave/<int:pk>/", views.leave_conversation_ajax, name="leave_conversation_ajax"),
]