from rest_framework import permissions,status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from meeting.models import Main, DjangoRelation, VotingResult
from meeting.ballot.get_ballot import get_ballot_data
from meeting.services.voting_service import get_summarized_voting_results


# Результаты голосования пользователя
class UserVotingResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, meeting_id, account_id):
        """Результаты голосования пользователя"""
        user = request.user
        meeting = get_object_or_404(Main, pk=meeting_id)
        ballot = get_ballot_data(meeting_id)

        is_registered = DjangoRelation.objects.filter(meeting=meeting, account_id=account_id, registered=True).exists()
        if not is_registered:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user.is_staff:
            # Администратор может смотреть результаты голосования по любому account_id в собрании
            result = VotingResult.objects.filter(meeting_id=meeting, account_id=account_id).first()
            if not result or result.json_result is None:
                return Response(
                    {"message": "Пользователь еще не проголосовал по этому account_id."},
                    status=status.HTTP_200_OK
                )
        else:
            # Обычный пользователь может смотреть только свои результаты голосования по доступному account_id
            result = VotingResult.objects.filter(meeting_id=meeting, account_id=account_id, user_id=user).first()
            if not result:
                return Response(status=status.HTTP_404_NOT_FOUND)  # Если голосов нет, просто 404

        return Response({
            "account_id": result.account_id,
            "data": ballot,
            "votes": result.json_result
        }, status=status.HTTP_200_OK)
    
# Суммарные результаты голосования по собранию
class AdminVotingResultsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, meeting_id):
        """Суммарные результаты голосования по собранию"""
        result = get_summarized_voting_results(meeting_id)

        if "error" in result:
            return Response({"message": result["error"]}, status=result["status"])

        return Response(result, status=result["status"])

    
