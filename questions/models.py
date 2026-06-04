from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Sum 

import os
import uuid

def avatar_upload_to(instance, filename):
    extension = filename.split(".")[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    now = timezone.now()
    date_path = timezone.now().strftime("%d/%m/%Y")
    return os.path.join("avatars", date_path, unique_name)

class DefaultModel(models.Model):
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(verbose_name="Дата обновления", auto_now=True)
    is_active = models.BooleanField(verbose_name="Активно?", default=True)
    
    class Meta:
        abstract = True

class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(verbose_name="Никнейм", max_length=50, unique=True, blank=True)
    bio = models.TextField(verbose_name="О себе", blank=True, max_length=500) 
    avatar = models.ImageField(verbose_name="Аватар", upload_to=avatar_upload_to, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль пользователя #{self.user_id}"
    
    def get_display_name(self):
        return self.nickname or self.user.username

class Tag(models.Model):
    name = models.CharField(verbose_name="Название", max_length=50, blank=False, unique=True, db_index=True)
    color = models.CharField(verbose_name="Цвет", max_length=7, default="#6c757d", blank=False)
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name
    
class QuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).select_related("author__profile").prefetch_related("tags")
        
    def new(self):
        return self.get_queryset().order_by('-created_at')
    
    def hot(self):
        return self.get_queryset().order_by("-likes_cnt", "-created_at")
        
    def by_tag(self, tag_name):
        return self.get_queryset().filter(tags__name=tag_name).order_by("-created_at")
    
class Question(DefaultModel):
    title = models.CharField(verbose_name="Заголовок", max_length=255, blank=False, db_index=True)
    text = models.TextField(verbose_name="Текст вопроса", blank=False, max_length=5000)
    author = models.ForeignKey(User, verbose_name="Автор", on_delete=models.SET_NULL, null=True, related_name="questions", db_index=True)
    tags = models.ManyToManyField(Tag, verbose_name="Теги", related_name="questions") 
    
    likes_cnt = models.IntegerField(verbose_name="Количество лайков", default=0, db_index=True)
    answers_cnt = models.IntegerField(verbose_name="Количество ответов", default=0, db_index=True)
    
    search_vector = SearchVectorField(null=True, editable=False)
    
    objects = QuestionManager()
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        
        indexes = [
            GinIndex(fields=['search_vector'], name='question_search_gin'),
        ]

    def __str__(self):
        if self.author_id:
            return f"Вопрос {self.title} от пользователя #{self.author_id}"
        return f"Вопрос {self.title} от удаленного пользователя"

    @property
    def net_rating(self):
        return self.likes_cnt
    
    def set_user_vote(self, user, value: int):
        like_obj, _ = QuestionLike.objects.get_or_create(user=user, question=self, defaults={'value': value})
        
        if value != like_obj.value:
            like_obj.value = value
            like_obj.save(update_fields=["value"])
            
            total = self.question_likes.aggregate(total=Sum('value'))['total'] or 0
            self.likes_cnt = total
            self.save(update_fields=['likes_cnt'])

class AnswerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).select_related("author__profile")
    
class Answer(DefaultModel):
    question = models.ForeignKey(Question, verbose_name="Вопрос", on_delete=models.CASCADE, related_name="answers", db_index=True)
    text = models.TextField(verbose_name="Текст ответа", blank=False, max_length=5000)
    author = models.ForeignKey(User, verbose_name="Автор", on_delete=models.SET_NULL, null=True, related_name="answers")
    is_approved = models.BooleanField(verbose_name="Одобренный ответ", default=False)
    
    likes_cnt = models.IntegerField(verbose_name="Количество лайков", default=0, db_index=True)
    
    objects = AnswerManager()
    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        if self.author_id:
            return f"Ответ на вопрос #{self.question_id} от пользователя #{self.author_id}"
        return f"Ответ на вопрос #{self.question_id} от удаленного пользователя"
    
    def update_question_answers_count(self):
        self.question.answers_cnt = self.question.answers.count()
        self.question.save(update_fields=['answers_cnt'])

    @property
    def net_rating(self):
        return self.likes_cnt
    
    def set_is_approved(self, value: bool):
        if self.is_approved != value:
            self.is_approved = value
            self.save(update_fields=["is_approved"])
            
    def set_user_vote(self, user, value: int):
        like_obj, _ = AnswerLike.objects.get_or_create(user=user, answer=self, defaults={'value': value})
        
        if value != like_obj.value:
            like_obj.value = value
            like_obj.save(update_fields=["value"])
            
            total = self.answer_likes.aggregate(total=Sum('value'))['total'] or 0
            self.likes_cnt = total
            self.save(update_fields=['likes_cnt'])
 
class AnswerLike(models.Model):
    answer = models.ForeignKey(Answer, verbose_name="Ответ", on_delete=models.CASCADE, related_name="answer_likes", db_index=True)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="user_answer_likes")
    value = models.SmallIntegerField(verbose_name="Оценка", choices=[(1, 'Лайк'), (-1, 'Дизлайк'), (0, 'Нет реакции')])
    created_at = models.DateTimeField(verbose_name="Дата реакции", auto_now_add=True, db_index=True)
    class Meta:
        unique_together = [
            ["user", "answer"]
        ]
        verbose_name = "Реакция на ответ"
        verbose_name_plural = "Реакции на ответ"

    def __str__(self):
        icon_map = {1: "👍", -1: "👎", 0: "😐"}
        icon = icon_map.get(self.value, "")
        return f"{icon} на ответ #{self.answer_id} от пользователя #{self.user_id}"
    
class QuestionLike(models.Model):
    question = models.ForeignKey(Question, verbose_name="Вопрос", on_delete=models.CASCADE, related_name="question_likes", db_index=True)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="user_question_likes")
    value = models.SmallIntegerField(verbose_name="Оценка", choices=[(1, 'Лайк'), (-1, 'Дизлайк'), (0, 'Нет реакции')])
    created_at = models.DateTimeField(verbose_name="Дата реакции", auto_now_add=True) 
    class Meta:
        unique_together = [
            ["user", "question"]
        ]
        verbose_name = "Реакция на вопрос"
        verbose_name_plural = "Реакции на вопрос"

    def __str__(self):
        icon_map = {1: "👍", -1: "👎", 0: "😐"}
        icon = icon_map.get(self.value, "")
        return f"{icon} на вопрос #{self.question_id} от пользователя #{self.user_id}"
    
