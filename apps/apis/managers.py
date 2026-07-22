from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

class ApiRequestLogQuerySet(models.QuerySet):
    def get_daily_stats(self, user, start_date):
        """Returns daily aggregated success and error counts for a user starting from start_date."""
        return self.filter(
            user=user,
            created_at__date__gte=start_date
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            success_count=Count('id', filter=Q(status_code=200)),
            error_count=Count('id', filter=~Q(status_code=200))
        )

    def get_service_distribution(self, user):
        """Returns aggregate distribution of API queries grouped by service for a user."""
        return self.filter(user=user)\
            .values('service_code', 'service_name')\
            .annotate(total=Count('id'))\
            .order_by('-total')

class ApiRequestLogManager(models.Manager):
    def get_queryset(self):
        return ApiRequestLogQuerySet(self.model, using=self._db)

    def get_daily_stats(self, user, start_date):
        return self.get_queryset().get_daily_stats(user, start_date)

    def get_service_distribution(self, user):
        return self.get_queryset().get_service_distribution(user)
