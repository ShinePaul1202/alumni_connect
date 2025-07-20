# core/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # The root URL now points to our new smart home view
    path('', views.home_view, name='home'),

    # Auth-related pages
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # App pages (require login)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_update_view, name='profile_update'),

    # --- PATHS FOR PASSWORD CHANGE ---
    path('account/password/change/', 
        auth_views.PasswordChangeView.as_view(
            template_name='core/account/change_password.html',
            success_url='/account/password/change/done/'
        ), 
        name='password_change'),
        
    path('account/password/change/done/', 
        auth_views.PasswordChangeDoneView.as_view(
            template_name='core/account/change_password_done.html'
        ), 
        name='password_change_done'),
]
