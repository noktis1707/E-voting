from rest_framework.generics import get_object_or_404
from meeting.models import Main, Agenda, QuestionDetail


# Получение бюллетеня (вопрос, решение, подвопросы и тд)
def get_ballot_data(meeting_id):
        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        # Повестка дня
        agenda = Agenda.objects.filter(meeting=meeting)

        # Структура бюллетеня
        ballot_data = {
            "meeting_id": meeting.meeting_id,
            "meeting_name": meeting.meeting_name,
            "deadline_date": meeting.deadline_date,
            "meeting_close": meeting.meeting_close,

            "agenda": []
        }

        for question in agenda:
            # Получение подвопросов (если есть)
            details = QuestionDetail.objects.filter(question_id=question.question_id, 
                                                    meeting_id=meeting ).values("detail_id", "detail_text")

            ballot_data["agenda"].append({
                "question_id": question.question_id,
                "question": question.question,
                "cumulative": question.cumulative,
                "decision": question.decision,
                "seat_count": question.seat_count,
                "details": list(details)
            })

        return ballot_data