from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

# Unregister the default User admin to use our custom one
admin.site.unregister(User)

# --- Admin Actions ---
@admin.action(description='Verify selected user profiles')
def verify_selected_profiles(modeladmin, request, queryset):
    """ Action to verify users and clear any fraud warnings. """
    profile_ids = queryset.values_list('profile__id', flat=True)
    Profile.objects.filter(id__in=profile_ids).update(is_verified=True, fraud_warning=None)
    modeladmin.message_user(request, "Selected users have been successfully verified.", messages.SUCCESS)

@admin.action(description='Mark selected users as fraudulent')
def mark_as_fraudulent(modeladmin, request, queryset):
    """ Action to un-verify users and add a fraud warning. """
    reason = "This account has been flagged for violating platform policies. Please contact support for assistance."
    profile_ids = queryset.values_list('profile__id', flat=True)
    Profile.objects.filter(id__in=profile_ids).update(is_verified=False, fraud_warning=reason)
    modeladmin.message_user(request, "Selected users have been marked as fraudulent.", messages.WARNING)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """ Custom User admin that includes Profile information. """

    class ProfileInline(admin.StackedInline):
        model = Profile
        can_delete = False
        verbose_name_plural = 'User Profile'
        fk_name = 'user'
        fieldsets = (
            (None, {'fields': ('avatar', 'full_name', 'bio')}),
            ('Academic & Professional Details', {'fields': ('user_type', 'department', 'graduation_year', 'is_verified')}),
            ('Work Experience', {'fields': ('currently_employed', 'job_title', 'company_name', 'had_past_job', 'past_job_title', 'past_company_name')}),
            ('Admin Controls', {'fields': ('fraud_warning',)}) # Fraud warning field
        )

    inlines = (ProfileInline,)
    actions = [verify_selected_profiles, mark_as_fraudulent]

    list_display = (
        'username', 'email', 'get_full_name', 'get_is_verified', 
        'get_user_type', 'get_department', 'get_graduation_year', 'is_staff'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'groups', 
        'profile__is_verified', 'profile__user_type', 'profile__department'
    )
    search_fields = ('username', 'email', 'profile__full_name')

    # Helper methods to display Profile data in the User list
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

    def get_graduation_year(self, instance):
        return instance.profile.graduation_year
    get_graduation_year.short_description = 'Grad Year'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)