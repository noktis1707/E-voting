from collections import defaultdict
from rest_framework import permissions,status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from meeting.models import Main, DjangoRelation, VotingResult
from meeting.ballot.get_ballot import get_ballot_data


# Результаты голосования пользователя
class UserVotingResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, meeting_id, account_id):
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
        meeting = get_object_or_404(Main, pk=meeting_id)
        ballot = get_ballot_data(meeting_id)

        # Получение всех результатов голосования по этому собранию
        results = VotingResult.objects.filter(meeting_id=meeting)

        if not results.exists():
            return Response({"message": "На этом собрании пока никто не голосовал."}, status=status.HTTP_404_NOT_FOUND)

        # Словарь для суммирования голосов
        summary_results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        # Обрабатывание каждого результата
        for result in results:
            if not result.json_result:  # Если json_result = None, пропускаем запись
                continue

            vote_details = result.json_result.get("VoteDtls", {}).get("VoteInstrForAgndRsltn", [])
            for vote in vote_details:
                vote_instr = vote.get("VoteInstr", {})
                question_id = vote_instr.get("QuestionId")
                detail_id = vote_instr.get("DetailId", None)  # Может отсутствовать
                
                # Определение типа голоса (For, Against, Abstain)
                for vote_type in ["For", "Against", "Abstain"]:
                    if vote_type in vote_instr:
                        quantity = int(vote_instr[vote_type]["Quantity"])
                        summary_results[question_id][detail_id][vote_type] += quantity

        # Формирование ответа
        response_data = []
        for question_id, details in summary_results.items():
            question_data = {"QuestionId": question_id, "results": []}
            for detail_id, votes in details.items():
                question_data["results"].append({
                    "DetailId": detail_id,
                    "For": votes.get("For", 0),
                    "Against": votes.get("Against", 0),
                    "Abstain": votes.get("Abstain", 0)
                })
            response_data.append(question_data)
        


        return Response({
            "data": ballot,
            "SummarizedVoteResults": response_data
        }, status=status.HTTP_200_OK)
    
