from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings



# =========================
# USER
# =========================
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('counselor', 'Counselor'),
        ('student', 'Student'),
    )

    service_number = models.CharField(max_length=50, blank=True, null=True)
    rank = models.CharField(max_length=50, blank=True, null=True)

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    school = models.CharField(max_length=100, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Auto-approve non-students
        if self.role in ['admin', 'counselor']:
            self.is_approved = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username


# =========================
# SPECIALIZATION
# =========================
class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# =========================
# COUNSELOR PROFILE
# =========================
class Counselor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='counselor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name()


# =========================
# APPOINTMENTS
# =========================
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    )

    student = models.ForeignKey(
        User,
        related_name='student_appointments',
        on_delete=models.CASCADE
    )
    counselor = models.ForeignKey(
        User,
        related_name='counselor_appointments',
        on_delete=models.CASCADE
    )
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)

    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.student} with {self.counselor} on {self.date}"


# =========================
# CHAT
# =========================
class ChatMessage(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"


# =========================
# ONLINE STATUS
# =========================

class UserStatus(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

# =========================
# CALL LOGS
# =========================
class CallLog(models.Model):
    CALL_TYPE_CHOICES = (
        ('voice', 'Voice'),
        ('video', 'Video'),
    )

    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    )

    caller = models.ForeignKey(
        User,
        related_name='calls_made',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User,
        related_name='calls_received',
        on_delete=models.CASCADE
    )

    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['call_type']),
        ]

    @property
    def duration(self):
        """
        Returns duration in seconds.
        Works for completed AND ongoing calls.
        """
        end_time = self.ended_at or timezone.now()
        return int((end_time - self.started_at).total_seconds())

    def __str__(self):
        return f"{self.caller} → {self.receiver} ({self.call_type}) [{self.status}]"


# =========================
# BOOKS
# =========================
class Book(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='books/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

