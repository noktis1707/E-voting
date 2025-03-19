from collections import defaultdict
from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from .permissions import IsAdminOrReadOnly
from .models import Main, DjangoRelation, VoteCount, Agenda, QuestionDetail, VotingResult
from .serializers import MeetingSerializer
from django.http import JsonResponse
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import action
# from rest_framework.response import Response

# Собрания
class MeetingView(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    # Для администратора список всех собраний
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Main.objects.all() 
        
        meeting_ids = DjangoRelation.objects.filter(user=user).values_list('meeting_id', flat=True)
        return Main.objects.filter(meeting_id__in=meeting_ids)
    
    # Для пользователя список собраний, в которых он может участвовать 
    def list(self, request, *args, **kwargs):
        user = request.user
        meetings = self.get_queryset()
        serialized_meetings = MeetingSerializer(meetings, many=True).data

        for meeting in serialized_meetings:
            meeting_id = meeting["meeting_id"]

            # Лицевые счета пользователя в этом собрании
            accounts = DjangoRelation.objects.filter(user=user, meeting_id=meeting_id).values_list("account_id", flat=True)

            # Список счетов с количеством голосов
            accounts_data = []
            for account_id in accounts:
                vote_count = VoteCount.objects.filter(meeting_id=meeting_id, account_id=account_id).first()
                json_quantity = vote_count.json_quantity if vote_count else {}

                accounts_data.append({
                    "account_id": account_id,
                    "votes": json_quantity  # Количество голосов
                })

            meeting["accounts"] = accounts_data  # Добавление лицевых счетов с голосами

        return Response(serialized_meetings)

# Создание собраний только для админа
class MeetingCreateView(viewsets.ModelViewSet):
    queryset = Main.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Создавать собрания могут только администраторы."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   
        

class MeetingUpdateView(generics.UpdateAPIView):
    queryset = Main.objects.all()
    serializer_class = MeetingSerializer
    def put(self, request,  *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Изменять собрания могут только администраторы."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Бюллетень
class VoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MeetingSerializer


    # Получение всех данный (собрание, повестка дня, подвопросы, лицевые счета, количество голосов) для конкретного пользователя
    def get(self, request, meeting_id, *args, **kwargs):
        user = request.user
        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        # Проверка зарегистрирован ли пользователь на этом собрании
        registrations = DjangoRelation.objects.filter(user=user, meeting=meeting, registered=True)

        if not registrations.exists():
            return Response(
                {"error": "Вы не зарегистрированы на это собрание."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Список account_id пользователя в этом собрании
        accounts = registrations.values_list("account_id", flat=True)

        # Повестка дня
        agenda = Agenda.objects.filter(meeting=meeting)

        # Структуру бюллетеня
        ballot_data = {
            "meeting_id": meeting.meeting_id,
            "meeting_name": meeting.meeting_name,
            "meeting_date": meeting.meeting_date,
            "agenda": []
        }

        for question in agenda:
            # Получение подвопросов (если есть)
            details = QuestionDetail.objects.filter(question_id=question.question_id).values("detail_id", "detail_text")

            ballot_data["agenda"].append({
                "question_id": question.question_id,
                "question": question.question,
                "cumulative": question.cumulative,
                "seat_count": question.seat_count,
                "details": list(details)
            })

        # Количество голосов
        accounts_data = []
        for account_id in accounts:
            vote_count = VoteCount.objects.filter(meeting=meeting, account_id=account_id).first()
            json_quantity = vote_count.json_quantity if vote_count else {}

            accounts_data.append({
                "account_id": account_id,
                "votes": json_quantity  # Количество голосов
            })

        # Добавляем лицевые счета пользователя
        ballot_data["accounts"] = accounts_data

        return Response(ballot_data, status=status.HTTP_200_OK)

    # Запись результатов
    def post(self, request, meeting_id, account_id):
        user = request.user
        vote_data = request.data.get("VoteDtls", {}).get("VoteInstrForAgndRsltn", [])

        if not vote_data:
            return Response({"error": "Нет данных для голосования."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, зарегистрирован ли пользователь
        is_registered = DjangoRelation.objects.filter(user=user, meeting=meeting_id, registered=True).exists()
        if not is_registered:
            return Response({"error": "Вы не зарегистрированы на этом собрании."}, status=status.HTTP_403_FORBIDDEN)

        # Проверяем, что у пользователя есть лицевые счета для голосования
        user_accounts = VoteCount.objects.filter(meeting=meeting_id, account_id__in=DjangoRelation.objects.filter(
            user=user, meeting=meeting_id
        ).values_list("account_id", flat=True))

        if not user_accounts.exists():
            return Response({"error": "У вас нет прав для голосования в этом собрании."}, status=status.HTTP_403_FORBIDDEN)

        # Проверяем, голосовал ли пользователь ранее
        existing_votes = VotingResult.objects.filter(
            meeting_id=meeting_id, account_id=account_id, user_id=user
        ).first()

        if existing_votes and existing_votes.json_result is not None:
            return Response({"error": "Вы уже проголосовали, повторное голосование невозможно."},
                            status=status.HTTP_403_FORBIDDEN)

        vote_json = {"VoteDtls": {"VoteInstrForAgndRsltn": []}}

        for vote_instr in vote_data:
            instr = vote_instr.get("VoteInstr", {})
            question_id = instr.get("QuestionId")
            detail_id = instr.get("DetailId", None)  # Для кумулятивного голосования

            # Проверка, существует ли вопрос в повестке дня
            question = get_object_or_404(Agenda, meeting_id=meeting_id, question_id=question_id)

            # Проверка, существует ли подвопрос (если передан detail_id)
            if detail_id:
                detail = get_object_or_404(QuestionDetail, question_id=question_id, detail_id=detail_id)

            # Определение типа голосования (За, Против, Воздержался)
            vote_types = ["For", "Against", "Abstain"]
            selected_type = next((t for t in vote_types if t in instr), None)

            if not selected_type:
                return Response({"error": f"Не указан тип голосования для QuestionId {question_id}."},
                                status=status.HTTP_400_BAD_REQUEST)

            vote_quantity = instr[selected_type].get("Quantity")
            if not vote_quantity:
                return Response({"error": f"Не указано количество голосов для QuestionId {question_id}."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Записываем голос в JSON
            vote_entry = {
                "VoteInstr": {
                    selected_type: {"Quantity": int(vote_quantity)},
                    "QuestionId": question_id
                }
            }
            if detail_id:
                vote_entry["VoteInstr"]["DetailId"] = detail_id

            vote_json["VoteDtls"]["VoteInstrForAgndRsltn"].append(vote_entry)

        meeting = get_object_or_404(Main, meeting_id=meeting_id)

        # Создаём записи в VotingResult по account_id
        if existing_votes:
            existing_votes.json_result = vote_json
            existing_votes.save()
        else:
            return Response({"error": "Ошибка: не найдена запись для обновления."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Ваш голос успешно сохранён."}, status=status.HTTP_201_CREATED)


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

# Результаты голосования пользователя
class UserVotingResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, meeting_id):
        user = request.user
        meeting = get_object_or_404(Main, pk=meeting_id)

        # Получение всех записей голосования пользователя по разным account_id
        results = VotingResult.objects.filter(meeting_id=meeting, user_id=user)

        if not results.exists():
            return Response({"message": "Вы не голосовали на этом собрании."}, status=status.HTTP_404_NOT_FOUND)

        # Формируем ответ с результатами голосования по каждому account_id
        response_data = []
        for result in results:
            response_data.append({
                "account_id": result.account_id,
                "votes": result.json_result
            })

        return Response({"VoteResults": response_data}, status=status.HTTP_200_OK)
    
# Суммарные результаты голосования по собранию
class AdminVotingResultsView(APIView):
    permission_classes = [permissions.IsAdminUser]  # Только администратор

    def get(self, request, meeting_id):
        meeting = get_object_or_404(Main, pk=meeting_id)

        # Получаем все результаты голосования по этому собранию
        results = VotingResult.objects.filter(meeting_id=meeting)

        if not results.exists():
            return Response({"message": "На этом собрании пока никто не голосовал."}, status=status.HTTP_404_NOT_FOUND)

        # Словарь для суммирования голосов
        summary_results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        # Обрабатываем каждый результат
        for result in results:
            if not result.json_result:  # Если json_result = None, пропускаем запись
                continue

            vote_details = result.json_result.get("VoteDtls", {}).get("VoteInstrForAgndRsltn", [])
            for vote in vote_details:
                vote_instr = vote.get("VoteInstr", {})
                question_id = vote_instr.get("QuestionId")
                detail_id = vote_instr.get("DetailId", None)  # Может отсутствовать
                
                # Определяем тип голоса (For, Against, Abstain)
                for vote_type in ["For", "Against", "Abstain"]:
                    if vote_type in vote_instr:
                        quantity = int(vote_instr[vote_type]["Quantity"])
                        summary_results[question_id][detail_id][vote_type] += quantity

        # Формируем ответ
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

        return Response({"SummarizedVoteResults": response_data}, status=status.HTTP_200_OK)
    
# Список зарегестрированных на собрании лиц (для админа)
class RegisteredUsersView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, meeting_id):
        meeting = get_object_or_404(Main, meeting_id=meeting_id)
        users_dict = []

        # Получаем account_fullname
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