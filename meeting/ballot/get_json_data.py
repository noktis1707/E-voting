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
        return json.dumps(result, ensure_ascii=False, indent=4)