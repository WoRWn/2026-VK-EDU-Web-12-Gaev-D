from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from questions.models import Profile, Tag, Question, Answer, AnswerLike, QuestionLike

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ["nickname", "bio", "avatar", "created_at"]
    readonly_fields = ["created_at"]
    can_delete = False
    extra = 0

class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ["author", "text", "is_approved", "created_at"]
    readonly_fields = ["created_at"]
    extra = 0
    
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email"]
    inlines = [ProfileInline]
        
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "nickname", "bio", "created_at"]
    search_fields = ["nickname", "bio", "user__username"]
    list_filter = ["created_at"]
    raw_id_fields = ["user"]
    
    list_select_related = ("user",)
    
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "questions_count"]
    search_fields = ["name"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_q_count=Count("questions"))

    @admin.display(description="Вопросов с тегом", ordering="_q_count")
    def questions_count(self, obj):
        return obj._q_count
    
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "get_tags"]
    search_fields = ["title", "author__username", "tags__name"]
    list_filter = ["author", "tags", "created_at"]
    raw_id_fields = ["author"]
    inlines = [AnswerInline]        
    
    list_select_related = ("author",)
    list_prefetch_related = ("tags",)

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = "Теги"
    
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "author", "created_at", "is_approved"]
    search_fields = ["text", "question__title", "author__username"]
    list_filter = ["author", "is_approved", "created_at"]
    raw_id_fields = ["question", "author"]
    
    list_select_related = ("question", "author")

@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "answer", "created_at"]
    search_fields = ["user__username"]
    list_filter = ["user", "answer", "created_at"]
    raw_id_fields = ["user", "answer"]
    
    list_select_related = ("user", "answer")

@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "question", "created_at"]
    search_fields = ["user__username", "question__title"]
    list_filter = ["user", "question", "created_at"]
    raw_id_fields = ["user", "question"]
    
    list_select_related = ("user", "question")