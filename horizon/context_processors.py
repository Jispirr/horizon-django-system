from .models import DealershipSettings, TestDriveRequest


def dealership_settings(request):
    """Inject dealership settings into every template context."""
    return {'dealership_settings': DealershipSettings.get()}


def pending_test_drives(request):
    """Inject unread test drive count for sidebar badge."""
    try:
        count = TestDriveRequest.objects.filter(is_read=False).count()
    except Exception:
        count = 0
    return {'sb_pending_test_drives': count}
