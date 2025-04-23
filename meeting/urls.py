from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import meeting, vote, register, results

router = SimpleRouter()

router.register('api/meetings', meeting.MeetingViewSet, basename='meetings')


urlpatterns = [  
    path('<int:meeting_id>/register/', register.RegisterForMeetingView.as_view(), name='register-for-meeting'),
    path('<int:meeting_id>/vote/<int:account_id>/', vote.VoteView.as_view(), name='meeting-vote'),
    # path('<int:meeting_id>/vote_results/', VotingResultsView.as_view(), name='vote-results'),
    path('<int:meeting_id>/vote_results/<int:account_id>/', results.UserVotingResultsView.as_view(), name='user-voting-results'),
    path('<int:meeting_id>/all_vote_results/', results.AdminVotingResultsView.as_view(), name='admin-voting-results'),
    path('<int:meeting_id>/registered_users/', register.RegisteredUsersView.as_view(), name='registered-users'),
]

urlpatterns += router.urls