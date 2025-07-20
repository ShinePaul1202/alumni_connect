from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

# First, unregister the old User admin to make way for our custom one.
admin.site.unregister(User)

@admin.action(description='Verify selected user profiles')
def verify_selected_profiles(modeladmin, request, queryset):
    """
    Custom action to verify the profiles associated with the selected users.
    """
    profile_ids = queryset.values_list('profile__id', flat=True)
    Profile.objects.filter(id__in=profile_ids).update(is_verified=True)

# This is our new, powerful User admin that combines User and Profile.
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    A custom User admin that displays Profile information and allows powerful filtering.
    """

    # --- LIST VIEW CONFIGURATION (with Graduation Year) ---
    list_display = (
        'username',
        'email',
        'get_full_name',
        'get_is_verified',
        'get_user_type',
        'get_department',
        'get_graduation_year', # CORRECTED: Added this field back
        'is_staff',
    )

    # --- FILTER AND SEARCH (with Graduation Year) ---
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'profile__is_verified',
        'profile__user_type',
        'profile__department',
        'profile__graduation_year', # CORRECTED: Added this field back
        'profile__currently_employed',
        'profile__had_past_job',
    )
    search_fields = (
        'username',
        'email',
        'profile__full_name',
        'profile__department',
    )
    
    # --- ACTIONS ---
    actions = [verify_selected_profiles]

    # --- PROFILE EDITING (The "Inline" part) ---
    class ProfileInline(admin.StackedInline):
        model = Profile
        can_delete = False
        verbose_name_plural = 'User Profile'
        fk_name = 'user'
        fieldsets = (
            (None, {'fields': ('avatar', 'full_name', 'bio')}),
            ('Academic & Professional Details', {'fields': ('user_type', 'department', 'graduation_year', 'is_verified')}),
            ('Work Experience', {'fields': ('currently_employed', 'job_title', 'company_name', 'had_past_job', 'past_job_title', 'past_company_name')}),
        )

    inlines = (ProfileInline,)

    # --- Helper methods to get data from the related Profile ---
    def get_full_name(self, instance):
        return instance.profile.full_name
    get_full_name.short_description = 'Full Name'

    def get_is_verified(self, instance):
        return instance.profile.is_verified
    get_is_verified.short_description = 'Verified'
    get_is_verified.boolean = True

    def get_user_type(self, instance):
        return instance.profile.user_type
    get_user_type.short_description = 'User Type'

    def get_department(self, instance):
        return instance.profile.department
    get_department.short_description = 'Department'

    # CORRECTED: Added the helper method for graduation year
    def get_graduation_year(self, instance):
        return instance.profile.graduation_year
    get_graduation_year.short_description = 'Grad Year'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)