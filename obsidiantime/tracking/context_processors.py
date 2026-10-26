from django.conf import settings
from django.urls import reverse

from .utils import get_consent, policy_version


def tracking_consent(request):
    """
    Выбор посетителя в баннере согласия и настройки для static/js/tracking.js
    """
    consent = get_consent(request)
    return {
        "tracking_consent": consent,
        "tracking_policy_version": policy_version(),
        "tracking_retention_days": settings.TRACKING["RETENTION_DAYS"],
        "tracking_config": {
            "consent": consent,
            "urls": {
                "consent": reverse("tracking:consent"),
                "collect": reverse("tracking:collect"),
                "myData": reverse("tracking:my_data"),
                "forget": reverse("tracking:forget"),
            },
        },
    }
