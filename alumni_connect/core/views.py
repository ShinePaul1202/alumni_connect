from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import RegistrationForm
from .models import Profile

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Get data from the validated form
            full_name = form.cleaned_data['full_name']
            # ✅ GET THE USERNAME FROM THE FORM
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # ✅ REMOVE THE OLD AUTO-GENERATION LOGIC
            # No need to generate a username anymore!

            # Create the user with the username they provided
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password)
            )

            # Create the associated profile
            Profile.objects.create(
                user=user,
                full_name=full_name,
                user_type=form.cleaned_data['user_type'],
                department=form.cleaned_data['department'],
                graduation_year=form.cleaned_data['graduation_year'],
                # ... (rest of the fields) ...
            )
            
            messages.success(request, 'Welcome aboard! Please sign in to continue.')
            return redirect('login')
    else:
        form = RegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

# --- Your login, logout, and dashboard views remain the same ---

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# ... (keep your register_view, logout_view, dashboard_view)

def login_view(request):
    if request.method == 'POST':
        # Get the identifier the user typed in (could be username or email)
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        user = None
        # ✅ NEW LOGIC: Check if the identifier looks like an email
        if '@' in identifier:
            # If it has an '@', we try to authenticate it as an email.
            # We need to find the user's username from their email first.
            try:
                from django.contrib.auth.models import User
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None # User with this email does not exist
        else:
            # If there's no '@', we treat it as a username.
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Provide a clear error message
            messages.error(request, "Invalid username/email or password. Please try again.")
            # Redirect back to the login page to show the message
            return redirect('login') 
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    profile = request.user.profile
    
    # ✅ CALCULATE REAL DATA
    # Count all profiles that are of type 'alumni' and are verified
    total_alumni_connections = Profile.objects.filter(user_type='alumni', is_verified=True).count()
    
    # You can add more calculations here later for messages, events, etc.
    # new_messages_count = ...
    
    context = {
        'profile': profile,
        'alumni_count': total_alumni_connections,
        # 'message_count': new_messages_count, # Example for the future
    }
    return render(request, 'core/dashboard.html', context)