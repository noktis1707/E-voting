from django.urls import path
from meeting import views
from rest_framework.routers import SimpleRouter

router = SimpleRouter()

router.register('', views.MeetingViewSet, basename='meetings')


urlpatterns = [  
    path('<int:meeting_id>/register/', views.RegisterForMeetingView.as_view(), name='register-for-meeting'),
    path('<int:meeting_id>/vote/<int:account_id>/', views.VoteView.as_view(), name='meeting-vote'),
    # path('<int:meeting_id>/vote_results/', VotingResultsView.as_view(), name='vote-results'),
    path('<int:meeting_id>/vote_results/<int:account_id>/', views.UserVotingResultsView.as_view(), name='user-voting-results'),
    path('<int:meeting_id>/all_vote_results/', views.AdminVotingResultsView.as_view(), name='admin-voting-results'),
    path('<int:meeting_id>/registered_users/', views.RegisteredUsersView.as_view(), name='registered-users'),
]

urlpatterns += router.urls