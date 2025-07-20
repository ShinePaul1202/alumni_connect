# core/urls.py
from django.urls import path
from . import views

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
]