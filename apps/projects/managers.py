from django.db import models


class ActiveProjectManager(models.Manager):
    """Default manager for project containers; soft-deleted projects stay hidden."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
