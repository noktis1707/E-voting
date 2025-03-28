from collections import defaultdict
from meeting.models import VotingResult, Main
from meeting.ballot.get_ballot import get_ballot_data
from django.shortcuts import get_object_or_404
from rest_framework import status

# Получение суммарных результатов голосования по собранию
def get_summarized_voting_results(meeting_id):
    meeting = get_object_or_404(Main, pk=meeting_id)
    ballot = get_ballot_data(meeting_id)

    results = VotingResult.objects.filter(meeting_id=meeting)

    if not results.exists():
        return {
            "error": "На этом собрании пока никто не голосовал.",
            "status": status.HTTP_404_NOT_FOUND
        }

    # Словарь для суммирования голосов
    summary_results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # Обрабатываем каждый результат голосования
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

    return {
        "data": ballot,
        "SummarizedVoteResults": response_data,
        "status": status.HTTP_200_OK
    }


