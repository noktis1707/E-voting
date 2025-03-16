from django.urls import path
from meeting import views


urlpatterns = [
    path('', views.MeetingView.as_view({'get': 'list'}), name='meetings'),
    path('create/', views.MeetingCreateView.as_view({'post': 'create'}), name='create-meeting'),
    path('<int:meeting_id>/', views.MeetingDetailView.as_view(), name='meeting-detail'),  # Получение конкретного собрания
    path('<int:meeting_id>/register/', views.RegisterForMeetingView.as_view(), name='register-for-meeting'),
    path('<int:meeting_id>/vote/<int:account_id>/', views.VoteView.as_view(), name='meeting-vote'),
    # path('<int:meeting_id>/vote_results/', VotingResultsView.as_view(), name='vote-results'),
    path('<int:meeting_id>/my_vote_results/', views.UserVotingResultsView.as_view(), name='user-voting-results'),
    path('<int:meeting_id>/vote_results/', views.AdminVotingResultsView.as_view(), name='admin-voting-results'),
]