# C:\project\alumni_connect\core\views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
# MODIFICATION: Imported the new form
from .forms import (
    RegistrationForm, UserUpdateForm, ProfileUpdateForm, SettingsForm, 
    AccountUserUpdateForm, AccountProfileUpdateForm, AccountProfileSettingsForm
)
from django.core.paginator import Paginator
from .models import Profile, Connection, Notification, SearchHistory
from .recommender import get_recommendations
from django.urls import reverse
from .decorators import verification_required
from messaging.models import Conversation

# --- AUTH & ROUTING VIEWS ---
def home_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'student':
            return redirect('core:student_dashboard')
        elif hasattr(request.user, 'profile') and request.user.profile.user_type == 'alumni':
            return redirect('core:alumni_dashboard')
        else:
            return redirect('core:logout')
    else:
        return render(request, 'core/index.html') 

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # --- THIS IS THE FIX ---
            # Determine the final department value
            department_value = cleaned_data.get('department')
            if department_value == 'OTHER':
                # If they chose "Other", use the text they entered
                final_department = cleaned_data.get('department_other')
            else:
                # Otherwise, use the value from the dropdown
                final_department = department_value

            full_name = cleaned_data.get('full_name', '')
            first_name = full_name.split()[0] if full_name else ''
            last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            
            new_user = User.objects.create_user(
                username=cleaned_data['username'], email=cleaned_data['email'],
                password=cleaned_data['password'], first_name=first_name, last_name=last_name
            )
            
            # Use the 'final_department' variable when creating the Profile
            Profile.objects.create(
                user=new_user, 
                full_name=full_name, 
                user_type=cleaned_data['user_type'],
                department=final_department, # <-- USE THE CORRECTED VARIABLE HERE
                graduation_year=cleaned_data.get('graduation_year'),
                # ... (rest of the fields are the same)
            )
            messages.success(request, 'Welcome aboard! Please sign in to continue.')
            return redirect('core:login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect('core:login')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('core:login')

# --- USER-SPECIFIC DASHBOARD AND PROFILE VIEWS ---
from .recommender import get_recommendations
from .models import Connection, Profile

@login_required
def student_dashboard_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "Your user profile could not be found. Please contact support.")
        logout(request)
        return redirect('core:login')

    if profile.is_verified and not profile.has_seen_verification_message:
        messages.success(request, "Congratulations! Your account has been successfully verified. You now have full access to the platform.")
        profile.has_seen_verification_message = True
        profile.save(update_fields=['has_seen_verification_message'])

    # --- Initialize all the data we need ---
    suggested_alumni = []
    recent_alumni = []
    connection_count = 0

    if profile.is_verified:
        # 1. Get alumni from the student's own department (your original logic)
        suggested_alumni = Profile.objects.filter(
            user_type='alumni', 
            is_verified=True, 
            department=profile.department
        ).exclude(user=request.user)

        # --- THIS IS THE NEW LOGIC TO ADD ---
        # 2. Get the 5 most recently joined alumni from ANY department
        recent_alumni = Profile.objects.filter(
            user_type='alumni', 
            is_verified=True
        ).exclude(user=request.user).order_by('-user__date_joined')[:5]
        # --- End of new logic ---

        # 3. Get the student's connection count (your original logic)
        connection_count = Connection.objects.filter(
            (Q(sender=request.user) | Q(receiver=request.user)),
            status=Connection.Status.ACCEPTED
        ).count()

    # --- THIS IS THE UPDATED CONTEXT ---
    context = {
        'profile': profile,
        'alumni_count': Profile.objects.filter(user_type='alumni', is_verified=True).count(),
        'suggested_alumni': suggested_alumni,
        'recent_alumni': recent_alumni, # <-- Pass the new list to the template
        'connection_count': connection_count,
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def alumni_dashboard_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "Your user profile could not be found. Please contact support.")
        logout(request)
        return redirect('core:login')

    if profile.is_verified and not profile.has_seen_verification_message:
        messages.success(request, "Congratulations! Your account has been successfully verified. You now have full access to the platform.")
        profile.has_seen_verification_message = True
        profile.save(update_fields=['has_seen_verification_message'])

    recent_alumni = []
    connection_count = 0
    student_message_count = 0

    if profile.is_verified:
        recent_alumni = Profile.objects.filter(
            user_type='alumni', is_verified=True
        ).exclude(user=request.user).order_by('-user__date_joined')[:5]

        # --- THIS IS THE NEW LOGIC THAT WAS MISSING ---

        # 1. Count accepted connections
        connection_count = Connection.objects.filter(
            (Q(sender=request.user) | Q(receiver=request.user)),
            status=Connection.Status.ACCEPTED
        ).count()

        # 2. Count unique conversations with students
        student_message_count = Conversation.objects.filter(
            participants=request.user
        ).filter(
            memberships__user__profile__user_type='student'
        ).distinct().count()

    # --- THIS IS THE UPDATED CONTEXT ---
    context = {
        'profile': profile,
        'recent_alumni': recent_alumni,
        'connection_count': connection_count,          # Pass the correct connection count
        'student_message_count': student_message_count  # Pass the correct student message count
    }
    return render(request, 'core/alumni_dashboard.html', context)

@login_required
def profile_view(request):
    # Get the logged-in user's profile
    user_profile = get_object_or_404(Profile, user=request.user)

    context = {
        'profile': user_profile,        # For the header/sidebar (logged-in user)
        'viewed_profile': user_profile  # For the main content (it's the same person!)
    }
    return render(request, 'core/profile_page.html', context)

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('core:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    profile = request.user.profile 
    context = { 'u_form': u_form, 'p_form': p_form, 'profile': profile }
    return render(request, 'core/profile_update.html', context)

@login_required
@verification_required
def profile_page_view(request, user_id):
    """
    Displays the profile page and checks the connection status between the
    viewer and the profile owner.
    """
    viewed_profile = get_object_or_404(Profile, user__id=user_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    context = {
        'profile': user_profile,
        'viewed_profile': viewed_profile,
        'connection': None  # Default to no connection
    }

    # --- THIS IS THE NEW LOGIC ---
    # We only check for a connection if the user is viewing someone else's profile. 
    if request.user.id != viewed_profile.user.id:
        # Find if a connection exists in either direction
        connection = Connection.objects.filter(
            (Q(sender=request.user, receiver=viewed_profile.user) | Q(sender=viewed_profile.user, receiver=request.user))
        ).first()
        context['connection'] = connection
    # --- END OF NEW LOGIC ---

    return render(request, 'core/profile_page.html', context)

@login_required
@verification_required
def find_alumni(request):
    user_profile = get_object_or_404(Profile, user=request.user)

    # --- THE FIX: Use .strip() to handle empty searches correctly ---
    department = request.GET.get("department", "").strip()
    graduation_year = request.GET.get("year", "").strip()
    company = request.GET.get("company", "").strip()

    # is_searching is now only True if at least one field has actual content
    is_searching = bool(department or graduation_year or company)

    # Save search history only if it's a real search
    if is_searching:
        SearchHistory.objects.create(
            user=request.user,
            department=department,
            graduation_year=graduation_year,
            company=company
        )

    if is_searching:
        # Step 1: Filter the alumni list based on the user's explicit query.
        base_queryset = Profile.objects.filter(
            is_verified=True, user_type="alumni"
        ).exclude(user=request.user)
        
        if department:
            base_queryset = base_queryset.filter(department__icontains=department)
        if graduation_year:
            try:
                base_queryset = base_queryset.filter(graduation_year=int(graduation_year))
            except (ValueError, TypeError):
                pass
        if company:
            base_queryset = base_queryset.filter(company_name__icontains=company)
        
        # Step 2: Rank the filtered results using the AI recommender
        recommendations = get_recommendations(user_profile, base_queryset=base_queryset)
        alumni_profiles_list = [rec['profile'] for rec in recommendations]

    else:
        # If the form is submitted with empty fields, this block will now run correctly
        recommendations = get_recommendations(user_profile)
        alumni_profiles_list = [rec['profile'] for rec in recommendations]
    
    # Step 3: Paginate the final list
    paginator = Paginator(alumni_profiles_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "profile": user_profile,
        "alumni_list": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
        "is_searching": is_searching,
    }
    return render(request, "core/find_alumni.html", context)

@login_required
@verification_required
def send_connection_request(request, user_id):
    """Send a connection request to the user with the given ID."""
    receiver = get_object_or_404(User, id=user_id)
    sender = request.user

    # Prevent sending request to oneself
    if receiver == sender:
        messages.error(request, "You cannot send a connection request to yourself.")
        return redirect('core:profile_page', user_id=user_id)

    # Prevent Alumni from sending requests to Students
    if sender.profile.user_type == 'alumni' and receiver.profile.user_type == 'student':
        messages.error(request, "Alumni cannot initiate connections with students.")
        return redirect('core:profile_page', user_id=user_id)

    # Check if a connection already exists (in either direction)
    existing_connection = Connection.objects.filter(
        (Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender))
    ).first()

    if existing_connection:
        messages.warning(request, "A connection request already exists with this user.")
        return redirect('core:profile_page', user_id=user_id)

    # Create the connection
    Connection.objects.create(sender=sender, receiver=receiver)
    messages.success(request, "Your connection request has been sent!")
    return redirect('core:profile_page', user_id=user_id)


@login_required
@verification_required
def connection_requests_list(request):
    """Display a list of pending connection requests for the logged-in user."""
    pending_requests = Connection.objects.filter(receiver=request.user, status=Connection.Status.PENDING)
    user_profile = get_object_or_404(Profile, user=request.user)
    context = {
        'requests': pending_requests,
        'profile': user_profile,  # Still need this for the image and verification check
    }
    return render(request, 'core/connection_requests.html', context)


@login_required
@verification_required
def respond_to_connection_request(request, request_id, action):
    connection_request = get_object_or_404(Connection, id=request_id, receiver=request.user)
    
    sender = connection_request.sender
    actor = request.user

    if action == "accept":
        connection_request.status = Connection.Status.ACCEPTED
        connection_request.save()
        messages.success(request, f"You are now connected with {sender.username}.")

        profile_link = request.build_absolute_uri(reverse('core:profile_page', kwargs={'user_id': actor.id}))
        Notification.objects.create(
            recipient=sender,
            actor=actor,
            verb='accepted your connection request.',
            link=profile_link
        )

        # --- NEW: Logic to send the email notification ---
        if sender.profile.email_on_connection_accepted:
            context = {
                'recipient_name': sender.profile.full_name or sender.username,
                'actor_name': actor.profile.full_name or actor.username,
                'profile_link': profile_link,
            }
            email_plain_text = render_to_string('core/emails/connection_accepted_email.txt', context)
            email_html = render_to_string('core/emails/connection_accepted_email.html', context)

            send_mail(
                subject=f"{actor.profile.full_name or actor.username} accepted your connection request!",
                message=email_plain_text,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[sender.email],
                html_message=email_html,
                fail_silently=False
            )
        # --- End of new email logic ---

    elif action == "decline":
        Notification.objects.create(
            recipient=sender,
            actor=actor,
            verb='declined your connection request.'
        )
        connection_request.delete()
        messages.info(request, "Connection request declined.")

    return redirect('core:connection_requests')

@login_required
@verification_required
def connection_list_view(request):
    """Displays a list of the user's accepted connections."""
    
    # Find all connections where the user is either the sender or receiver
    # and the status is 'accepted'.
    connections = Connection.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)),
        status=Connection.Status.ACCEPTED
    )

    # From these connections, get the list of the *other* users' profiles.
    connection_profiles = []
    for conn in connections:
        if conn.sender == request.user:
            connection_profiles.append(conn.receiver.profile)
        else:
            connection_profiles.append(conn.sender.profile)

    context = {
        'profile': request.user.profile,
        'connection_profiles': connection_profiles
    }
    return render(request, 'core/connection_list.html', context)


@login_required
def notification_list_view(request):
    """Display a list of notifications and mark them as read."""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark all unread notifications as read when the user views the page
    notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'core/notifications.html', {
        'notifications': notifications,
        'profile': request.user.profile # For the sidebar
    })

@login_required
def settings_home_view(request):
    
    """
    Displays the main settings menu page.
    """
    context = {
        'profile': request.user.profile
    }
    return render(request, 'core/account/settings_home.html', context)

# --- MODIFIED VIEW TO HANDLE NEW PROFILE FIELDS ---
@login_required
def account_details_view(request):
    """
    Handles updating the user's non-sensitive account info like email, department, etc.
    This view corresponds to the "Account Details" tab.
    """
    profile = request.user.profile

    # This condition is TRUE only if the user has NOT used their one-time edit yet,
    # AND their account is either unverified OR has a fraud warning.
    can_edit_critical_details = (
        not profile.has_edited_critical_details and
        (not profile.is_verified or profile.fraud_warning)
    )

    if request.method == 'POST':
        # We use the forms you already created
        user_form = AccountUserUpdateForm(request.POST, instance=request.user)
        profile_form = AccountProfileSettingsForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            if can_edit_critical_details:
                # Check which fields the user actually changed in the form submission.
                changed_data = user_form.changed_data + profile_form.changed_data
                critical_fields = ['username', 'department', 'graduation_year']
                
                # If any of the critical fields were modified, set the flag to True.
                # This will prevent future edits.
                if any(field in changed_data for field in critical_fields):
                    profile.has_edited_critical_details = True

            user_form.save()
            profile_form.save()
            messages.success(request, 'Your account details have been updated successfully.')
            return redirect('core:account_details') # Redirect back to the same page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # For a GET request, create instances of the forms with current user data
        user_form = AccountUserUpdateForm(instance=request.user)
        profile_form = AccountProfileSettingsForm(instance=request.user.profile)

    if not can_edit_critical_details:
        user_form.fields['username'].disabled = True
        profile_form.fields['department'].disabled = True
        profile_form.fields['graduation_year'].disabled = True

    context = {
        'profile': request.user.profile,
        'user_form': user_form,
        'profile_form': profile_form,
        'active_tab': 'details',  # This is used by the template to highlight the correct link
        'can_edit_critical_details': can_edit_critical_details,  # Pass this to the template
    }
    return render(request, 'core/account/settings_details.html', context)


@login_required
def password_security_view(request):
    """
    Handles changing the user's password.
    This view corresponds to the "Password & Security" tab.
    """
    if request.method == 'POST':
        # Django's built-in form is perfect for this
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keeps the user logged in
            messages.success(request, 'Your password was successfully updated.')
            return redirect('core:password_security') # Redirect back to the same page
        else:
            messages.error(request, 'There was an error updating your password. Please check the details below.')
    else:
        password_form = PasswordChangeForm(request.user)

    for field_name, field in password_form.fields.items():
        field.widget.attrs.update({'class': 'form-control'})

    context = {
        'profile': request.user.profile,
        'password_form': password_form,
        'active_tab': 'password'
    }
    return render(request, 'core/account/settings_password.html', context)


@login_required
def notification_settings_view(request):
    """
    Handles updating the user's notification preferences.
    This view corresponds to the "Notifications" tab.
    """
    if request.method == 'POST':
        # We use the SettingsForm you already created
        settings_form = SettingsForm(request.POST, instance=request.user.profile)
        if settings_form.is_valid():
            settings_form.save()
            messages.success(request, 'Your notification settings have been updated.')
            return redirect('core:notification_settings') # Redirect back to the same page
    else:
        settings_form = SettingsForm(instance=request.user.profile)

    context = {
        'profile': request.user.profile,
        'settings_form': settings_form,
        'active_tab': 'notifications'
    }
    return render(request, 'core/account/settings_notifications.html', context)

