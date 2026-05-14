from django.urls import path
from questions.views import IndexPageView, HotPageView, TagPageView, QuestionPageView, AskPageView, like_question, like_answer, mark_correct_answer

urlpatterns = [
    path('', IndexPageView.as_view(), name='index'),
    path('hot/', HotPageView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', TagPageView.as_view(), name='tag'),
    path('question/<int:question_id>/', QuestionPageView.as_view(), name='question'),
    path('ask/', AskPageView.as_view(), name='ask'),
    
    path('question/like/', like_question, name='like_question'),
    path('answer/like/', like_answer, name='like_answer'),
    path('answer/mark-correct/', mark_correct_answer, name='mark_correct_answer')
]
