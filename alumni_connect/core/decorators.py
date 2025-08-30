from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def verification_required(view_func):
    """
    Decorator to ensure a user is verified and not marked as fraudulent
    before accessing a view.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user has a profile and is authenticated
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            # This should be handled by @login_required, but it's a good safeguard
            return redirect('core:login')

        profile = request.user.profile
        
        # THE CORE LOGIC: Check if the user is unverified OR has a fraud warning
        if not profile.is_verified or profile.fraud_warning:
            # If they are in a limited state, show an error and redirect them
            messages.error(request, "You must be a verified user to access this page.")
            
            # Redirect to their specific dashboard
            if profile.user_type == 'student':
                return redirect('core:student_dashboard')
            else:
                return redirect('core:alumni_dashboard')
        
        # If they are verified and not fraudulent, allow them to access the view
        return view_func(request, *args, **kwargs)

    return _wrapped_view