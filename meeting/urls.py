from django.urls import path
from meeting.views import MeetingViewSet, MeetingDetailView, UserMeetingsWithAccountsView


urlpatterns = [
    path('', MeetingViewSet.as_view({'get': 'list', 'post': 'create'}), name='meetings'),
    path('<int:meeting_id>/', MeetingDetailView.as_view(), name='meeting-detail'),  # Получение конкретного собрания
    path('meetings/user_with_accounts/', UserMeetingsWithAccountsView.as_view({'get': 'list'})),
    # path('meetings/create/', MeetingViewSet.as_view(), name='create_meeting'),
]