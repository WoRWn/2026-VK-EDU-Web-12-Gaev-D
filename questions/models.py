from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Sum

import os
import uuid

def avatar_upload_to(instance, filename):
    extension = filename.split(".")[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    return os.path.join("avatars", unique_name)

class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(verbose_name="Никнейм", max_length=50, unique=True, blank=True)
    bio = models.CharField(verbose_name="О себе", max_length=500, blank=True)
    avatar = models.ImageField(verbose_name="Аватар", upload_to=avatar_upload_to, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"

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
        return super().get_queryset().select_related("author__profile").prefetch_related("tags")
        
    def new(self):
        return self.get_queryset().annotate(
            answers_count=Count("answers", distinct=True), 
            likes_count=Count("question_likes", distinct=True)
            ).order_by('-created_at')
    
    def hot(self):
        return self.get_queryset().annotate(
            answers_count=Count("answers", distinct=True), 
            likes_count=Count("question_likes", distinct=True)
            ).order_by("-likes_count", "-created_at")
        
    def by_tag(self, tag_name):
        return self.get_queryset().annotate(
            answers_count=Count("answers", distinct=True), 
            likes_count=Count("question_likes", distinct=True)            
        ).filter(tags__name=tag_name).order_by("-created_at")
    
class Question(models.Model):
    title = models.CharField(verbose_name="Заголовок", max_length=255, blank=False, db_index=True)
    text = models.TextField(verbose_name="Текст вопроса", blank=False)
    author = models.ForeignKey(User, verbose_name="Автор", on_delete=models.CASCADE, related_name="questions", db_index=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, db_index=True)   
    tags = models.ManyToManyField(Tag, verbose_name="Теги", related_name="questions") 
    
    objects = QuestionManager()
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.title

    @property
    def net_rating(self):
        res = self.question_likes.aggregate(total=Sum('value'))
        return res['total'] or 0

class Answer(models.Model):
    question = models.ForeignKey(Question, verbose_name="Вопрос", on_delete=models.CASCADE, related_name="answers", db_index=True)
    text = models.TextField(verbose_name="Текст ответа", blank=False)
    author = models.ForeignKey(User, verbose_name="Автор", on_delete=models.CASCADE, related_name="answers")
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True, db_index=True)    
    is_approved = models.BooleanField(verbose_name="Одобренный ответ", default=False)
    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ на {self.question.title} от {self.author.username}"

    @property
    def net_rating(self):
        res = self.answer_likes.aggregate(total=Sum('value'))
        return res['total'] or 0
    
class AnswerLike(models.Model):
    answer = models.ForeignKey(Answer, verbose_name="Ответ", on_delete=models.CASCADE, related_name="answer_likes", db_index=True)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="user_answer_likes")
    value = models.SmallIntegerField(verbose_name="Оценка", choices=[(1, 'Лайк'), (-1, 'Дизлайк')])
    created_at = models.DateTimeField(verbose_name="Дата реакции", auto_now_add=True, db_index=True)
    class Meta:
        unique_together = [
            ["user", "answer"]
        ]
        verbose_name = "Реакция на ответ"
        verbose_name_plural = "Реакции на ответ"

    def __str__(self):
        return f"{'👍' if self.value > 0 else '👎'} на {self.answer} от {self.user}"
    
class QuestionLike(models.Model):
    question = models.ForeignKey(Question, verbose_name="Вопрос", on_delete=models.CASCADE, related_name="question_likes", db_index=True)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="user_question_likes")
    value = models.SmallIntegerField(verbose_name="Оценка", choices=[(1, 'Лайк'), (-1, 'Дизлайк')])
    created_at = models.DateTimeField(verbose_name="Дата реакции", auto_now_add=True) 
    class Meta:
        unique_together = [
            ["user", "question"]
        ]
        verbose_name = "Реакция на вопрос"
        verbose_name_plural = "Реакции на вопрос"

    def __str__(self):
        return f"{'👍' if self.value > 0 else '👎'} на {self.question.title} от {self.user}"