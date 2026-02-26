from .models import UserStatus
from django.utils import timezone


class OnlineNowMiddleware:
    """
    Middleware to update the user's online status automatically.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only track authenticated users
        if request.user.is_authenticated and request.user.role == 'counselor':
            # Get or create status object
            status, _ = UserStatus.objects.get_or_create(user=request.user)
            status.is_online = True
            status.last_seen = timezone.now()
            status.save()

        response = self.get_response(request)

        # Optional: mark offline after response if you want
        # But better to use a periodic task or JavaScript ping
        return response
