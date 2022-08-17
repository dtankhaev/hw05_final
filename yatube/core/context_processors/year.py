from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    a = timezone.now()
    return {
        'year': a.year
    }
