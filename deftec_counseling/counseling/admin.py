from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Specialization, Appointment, ChatMessage, UserStatus, Counselor

# =========================
# CUSTOM USER ADMIN
# =========================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'role', 'is_approved', 'get_specialization')
    list_filter = ('role', 'is_approved')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('service_number', 'rank', 'school', 'class_name', 'role', 'is_approved')}),
    )
    actions = ['approve_students']

    def approve_students(self, request, queryset):
        queryset.filter(role='student', is_approved=False).update(is_approved=True)
    approve_students.short_description = "Approve selected students"

    # -------------------------
    # Get specialization safely
    # -------------------------
    def get_specialization(self, obj):
        if hasattr(obj, 'counselor_profile') and obj.counselor_profile:
            return obj.counselor_profile.specialization
        return None
    get_specialization.short_description = 'Specialization'

# =========================
# SPECIALIZATION ADMIN
# =========================
@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

# =========================
# APPOINTMENTS ADMIN
# =========================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'counselor', 'specialization', 'date', 'time', 'status')

# =========================
# CHAT MESSAGES ADMIN
# =========================
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'sender', 'message', 'timestamp')

# =========================
# USER STATUS ADMIN
# =========================
@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online')
