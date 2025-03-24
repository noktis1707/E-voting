from rest_framework import permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from meeting.models import Main, DjangoRelation, VoteCount
from meeting.ballot.get_ballot import get_ballot_data

# Регистрация в собрании
class RegisterForMeetingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, meeting_id, *args, **kwargs):
        user = request.user
        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        if meeting.status != 2:
            return Response({"error": "Регистрация не разрешена."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на наличие связей
        registrations = DjangoRelation.objects.filter(user=user, meeting=meeting)

        if not registrations.exists():
            return Response(
                {"error": "Вы не можете зарегистрироваться, так как не связаны с этим собранием."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка, зарегистрирован ли он уже по всем записям
        already_registered = all(registration.registered for registration in registrations)

        if already_registered:
            return Response(
                {"error": "Вы уже зарегистрированы на это собрание."},
                status=status.HTTP_400_BAD_REQUEST
            )

        registrations.update(registered=True)

        return Response({"message": "Вы успешно зарегистрированы на собрание."}, status=status.HTTP_200_OK)
    

# Список зарегестрированных на собрании лиц (для админа)
class RegisteredUsersView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        meeting_id =  self.kwargs.get("meeting_id")  
        meeting = get_object_or_404(Main, meeting_id=meeting_id)
        users_dict = []

        # Получение account_fullname
        account_info = {
            (vote.account_id, vote.meeting_id): vote.account_fullname
            for vote in VoteCount.objects.filter(meeting=meeting)
        }

        for relation in DjangoRelation.objects.filter(meeting=meeting, registered=True).select_related("user"):
            
            account_fullname = account_info.get((relation.account_id, meeting.meeting_id), "Неизвестный счёт")
            users_dict.append({
                "account_id": relation.account_id,
                "account_fullname": account_fullname
            })

        return Response(users_dict, status=status.HTTP_200_OK)
