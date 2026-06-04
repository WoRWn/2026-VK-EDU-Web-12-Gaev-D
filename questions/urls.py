from django.urls import path
from questions.views import IndexPageView, HotPageView, TagPageView, QuestionPageView, AskPageView, LikeQuestionView, LikeAnswerView, MarkCorrectAnswerView, search_suggestions

urlpatterns = [
    path('', IndexPageView.as_view(), name='index'),
    path('hot/', HotPageView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', TagPageView.as_view(), name='tag'),
    path('question/<int:question_id>/', QuestionPageView.as_view(), name='question'),
    path('ask/', AskPageView.as_view(), name='ask'),
    
    path('question/<int:question_id>/like/', LikeQuestionView.as_view(), name='question_like'),
    path('question/<int:question_id>/answer/<int:answer_id>/like/', LikeAnswerView.as_view(), name='answer_like'),
    path('question/<int:question_id>/answer/<int:answer_id>/mark-correct/', MarkCorrectAnswerView.as_view(), name='mark_correct'),
    
    path('api/search/', search_suggestions, name='search'),
]
