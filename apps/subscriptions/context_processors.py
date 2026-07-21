from .services import get_user_usage_summary


def user_subscription(request):
    """
    Inyecta información sobre la suscripción y el uso mensual del usuario en el contexto de las plantillas.
    """
    if request.user.is_authenticated:
        try:
            usage_summary = get_user_usage_summary(request.user)
            return {'user_usage': usage_summary}
        except Exception:
            return {'user_usage': None}
    return {'user_usage': None}
