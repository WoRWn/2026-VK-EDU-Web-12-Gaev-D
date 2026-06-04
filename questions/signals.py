from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from questions.models import Question
    
@receiver(post_save, sender=Question)
def update_search_vector(sender, instance, created, **kwargs):
    Question.objects.filter(id=instance.id).update(
        search_vector=(
            SearchVector('title', weight='A', config='russian') +
            SearchVector('text', weight='B', config='russian')
        )
    )