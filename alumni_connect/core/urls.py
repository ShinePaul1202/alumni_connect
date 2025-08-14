# core/urls.py

from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    # Main routing and auth
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Role-specific dashboard URLs
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('alumni/dashboard/', views.alumni_dashboard_view, name='alumni_dashboard'),

    # Profile viewing and updating
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('profile/', views.profile_view, name='profile'),
    
    # Settings and Password Change
    path('settings/', views.settings_view, name='settings'),
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
        
    # === PASSWORD RESET URLS (CORRECTED FOR HTML EMAIL) ===
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
            template_name='core/password_reset.html',
            # This points to the plain text fallback version
            email_template_name='core/password_reset_email.txt',
            # This points to the styled HTML version
            html_email_template_name='core/password_reset_email.html',
            success_url=reverse_lazy('core:password_reset_done') 
         ), 
         name='password_reset'),

    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
            template_name='core/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html',
            success_url=reverse_lazy('core:password_reset_complete')
         ), 
         name='password_reset_confirm'),

    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
            template_name='core/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]