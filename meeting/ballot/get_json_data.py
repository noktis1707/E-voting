from .get_ballot import get_ballot_data
import json



def get_json_data(meeting_id, quantity):
         
        data = get_ballot_data(meeting_id)

        # Инициализируем результат
        result = {
            "VoteDtls": {
                "VoteInstrForAgndRsltn": []
            }
        }

        # Преобразуем agenda в нужный формат
        for question in data["agenda"]:
            if question["details"]:
                # Если есть подвопросы
                for detail in question["details"]:
                    result["VoteDtls"]["VoteInstrForAgndRsltn"].append({
                        "VoteInstr": {
                            "DetailId": detail["detail_id"],
                            "Quantity": quantity,
                            "QuestionId": question["question_id"]
                        }
                    })
            else:
                # Если подвопросов нет, добавляем просто вопрос
                result["VoteDtls"]["VoteInstrForAgndRsltn"].append({
                    "VoteInstr": {
                        "Quantity": quantity,
                        "QuestionId": question["question_id"]
                    }
                })

        # Возвращаем JSON в нужном формате
        return json.dumps(result, ensure_ascii=False, indent=4).replace("\n", " ")
        # return result



from meeting.models import VotingResult, DjangoRelation, VoteCount
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_voting_result_and_relation(vote_count_id: int, user_id: int):
    """
    Создаёт VotingResult и DjangoRelation по ID записи VoteCount и user_id.
    """
    try:
        vote_count = VoteCount.objects.get(pk=vote_count_id)
    except VoteCount.DoesNotExist:
        raise ValueError(f"VoteCount с id={vote_count_id} не найден.")

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValueError(f"Пользователь с id={user_id} не найден.")

    with transaction.atomic():
        voting_result, _ = VotingResult.objects.get_or_create(
            meeting_id=vote_count.meeting,
            account_id=vote_count.account_id,
            user_id=user
        )

        DjangoRelation.objects.get_or_create(
            vote_count=vote_count,
            voting_result=voting_result,
            user=user,
            meeting=vote_count.meeting,
            account_id=vote_count.account_id
        ) 

    return voting_result