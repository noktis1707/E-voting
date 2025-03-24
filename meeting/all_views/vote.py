from rest_framework import  permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from meeting.models import Main, DjangoRelation, VoteCount, VotingResult
from meeting.serializers import MeetingSerializer
from meeting.ballot.get_ballot import get_ballot_data


# Бюллетень
class VoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MeetingSerializer

    # Получение всех данных (собрание, повестка дня, подвопросы, количество голосов) для конкретного пользователя
    def get(self, request, meeting_id, account_id, *args, **kwargs):
        user = request.user
        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        # Проверка статуса собрания
        if not meeting.allowed_voting:
            return Response({"error": "Голосование сейчас недоступно."}, status=status.HTTP_403_FORBIDDEN)

        # Проверка зарегистрирован ли пользователь на этом собрании
        registrations = DjangoRelation.objects.filter(user=user, meeting=meeting, registered=True)

        if not registrations.exists():
            return Response(
                {"error": "Вы не зарегистрированы на это собрание."},
                status=status.HTTP_403_FORBIDDEN
            )

        ballot_data = get_ballot_data(meeting_id)

        # Количество голосов
        vote_count = VoteCount.objects.filter(meeting=meeting, account_id=account_id).first()
        json_quantity = vote_count.json_quantity if vote_count else {}

        ballot_data["vote_count"] = json_quantity


        return Response(ballot_data, status=status.HTTP_200_OK)

    # Запись результатов
    def post(self, request, meeting_id, account_id):
        user = request.user
        vote_data = request.data
        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        # Проверка статуса собрания (должен быть "Разрешено голосование")
        if not meeting.allowed_voting:
            return Response({"error": "Голосование сейчас недоступно."}, status=status.HTTP_403_FORBIDDEN)         

        if not vote_data:
            return Response({"error": "Нет данных для голосования."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, зарегистрирован ли пользователь
        is_registered = DjangoRelation.objects.filter(user=user, meeting=meeting_id, registered=True).exists()
        if not is_registered:
            return Response({"error": "Вы не зарегистрированы на этом собрании."}, status=status.HTTP_403_FORBIDDEN)

        # Проверка, что у пользователя есть лицевые счета для голосования
        user_accounts = VoteCount.objects.filter(meeting=meeting_id, account_id__in=DjangoRelation.objects.filter(
            user=user, meeting=meeting_id
        ).values_list("account_id", flat=True))

        if not user_accounts.exists():
            return Response({"error": "У вас нет прав для голосования в этом собрании."}, status=status.HTTP_403_FORBIDDEN)

        # Проверка, голосовал ли пользователь ранее
        existing_votes = VotingResult.objects.filter(
            meeting_id=meeting_id, account_id=account_id, user_id=user
        ).first()

        if existing_votes and existing_votes.json_result is not None:
            return Response({"error": "Вы уже проголосовали, повторное голосование невозможно."},
                            status=status.HTTP_403_FORBIDDEN)
        
        if existing_votes:
            existing_votes.json_result = vote_data
            existing_votes.save()

        return Response({"message": "Ваш голос успешно сохранён."}, status=status.HTTP_201_CREATED)
