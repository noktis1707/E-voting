from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from .models import Main, DjangoRelation, VoteCount
from .serializers import MeetingSerializer
from django.http import JsonResponse
from rest_framework.views import APIView
# from rest_framework.response import Response

class MeetingViewSet(viewsets.ModelViewSet, APIView):
    queryset = Main.objects.all()
    serializer_class = MeetingSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        meeting_id = request.query_params.get('meeting_id')

        if meeting_id: 
            meeting = Main.objects.get(meeting_id=meeting_id)
            serialized_meetings = MeetingSerializer(meeting)
            return Response({"items": serialized_meetings.data})
            
        meetings = Main.objects.all()
        serialized_meetings = MeetingSerializer(meetings, many=True)
        return JsonResponse({"items": serialized_meetings.data})
    
    # def post(self, request):
    #     serializer = MeetingSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeetingDetailView(generics.RetrieveAPIView):
    queryset = Main.objects.all()
    serializer_class = MeetingSerializer
    lookup_field = 'meeting_id'  # Поле для поиска записи

class UserMeetingsWithAccountsView(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user

        # Получаем собрания, в которых участвует пользователь
        meetings = Main.objects.filter(djangorelation__user=user).distinct()

        response_data = []

        for meeting in meetings:
            # Получаем лицевые счета пользователя для этого собрания
            accounts = DjangoRelation.objects.filter(user=user, meeting=meeting).values_list('account_id', flat=True)

            # Получаем количество голосов по лицевым счетам
            vote_counts = VoteCount.objects.filter(meeting=meeting, account_id__in=accounts).values('account_id', 'account_fullname', 'json_quantity')

            response_data.append({
                "meeting_id": meeting.meeting_id,
                "meeting_name": meeting.meeting_name,
                "meeting_date": meeting.meeting_date,
                "accounts": list(vote_counts)
            })

        return Response(response_data)