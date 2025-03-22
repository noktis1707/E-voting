from collections import defaultdict
from rest_framework import viewsets, permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from django.db import transaction

from .permissions import IsAdminOrReadOnly
from .models import Main, DjangoRelation, VoteCount, Agenda, QuestionDetail, VotingResult
from .serializers import MeetingSerializer, MeetingListSerializer
from .ballot.get_ballot import get_ballot_data

# Собрания
class MeetingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'drafts']:
            return MeetingListSerializer  # Для списка собраний
        return MeetingSerializer  # Для детального просмотра

    def get_queryset(self):
        user = self.request.user

        # Для администратора список всех собраний, которые не являются черновиками
        if user.is_staff:
            return Main.objects.filter(is_draft=False) 
            # return Main.objects.all() 
        
        # Для участника список собраний, в которых он может участвовать и которые не являются черновиками
        meeting_ids = DjangoRelation.objects.filter(user=user).values_list('meeting_id', flat=True)
        return Main.objects.filter(meeting_id__in=meeting_ids, is_draft=False)
    
    # Черновики все (только админ)
    @action(detail=False, methods=['get'], url_path='drafts', permission_classes=[permissions.IsAdminUser])
    def drafts(self, request):
        drafts = Main.objects.filter(is_draft=True)
        serializer = MeetingListSerializer(drafts, many=True)
        return Response(serializer.data)
    
    # Конкретный черновик (только админ) для возможного редактирования
    @action(detail=True, methods=['get', 'put', 'patch'], url_path='draft', permission_classes=[permissions.IsAdminUser])
    def draft_detail(self, request, pk=None):
        meeting = Main.objects.get(pk=pk)

        if not meeting.is_draft:
            return Response({"error": "Это не черновик."}, status=status.HTTP_400_BAD_REQUEST)

        # Вернуть заполненные данные черновика
        if request.method == 'GET':
            serializer = MeetingSerializer(meeting)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Обновление данных черновика
        if request.method in ['PUT', 'PATCH']:
            meeting_data = request.data.copy()
            agenda_data = meeting_data.pop('agenda', [])

            # Обновление данных собрания
            serializer = MeetingSerializer(meeting, data=meeting_data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    # Сохранение изменений в собрании
                    serializer.save()

                    # Обновление повестки дня
                    existing_agenda_ids = set(Agenda.objects.filter(meeting=meeting).values_list('question_id', flat=True))
                    updated_agenda_ids = set()

                    for agenda_item in agenda_data:
                        question_id = agenda_item.get("question_id")
                        details_data = agenda_item.pop("details", [])

                        seat_count = len(details_data)  

                        # Если вопрос уже существует, обновляем его
                        if question_id and question_id in existing_agenda_ids:
                            agenda_instance = Agenda.objects.get(question_id=question_id, meeting=meeting)
                            for key, value in agenda_item.items():
                                setattr(agenda_instance, key, value)
                            agenda_instance.seat_count = seat_count 
                            agenda_instance.save()
                        else:
                            # Создание нового вопроса
                            agenda_instance = Agenda.objects.create(meeting=meeting, seat_count=seat_count, **agenda_item)

                        updated_agenda_ids.add(agenda_instance.question_id)

                        # Обновление подвопросов
                        existing_details = {d.detail_id for d in QuestionDetail.objects.filter(question_id=agenda_instance)}
                        updated_details = set()

                        for detail in details_data:
                            detail_id = detail.get("detail_id")

                            if detail_id and detail_id in existing_details:
                                detail_instance = QuestionDetail.objects.get(detail_id=detail_id)
                                detail_instance.detail_text = detail.get("detail_text", detail_instance.detail_text)
                                detail_instance.save()
                            else:
                                detail_instance = QuestionDetail.objects.create(question_id=agenda_instance, meeting_id=meeting, **detail)

                            updated_details.add(detail_instance.detail_id)

                        # Удаление подвопросов, которых нет в новом списке
                        QuestionDetail.objects.filter(question_id=agenda_instance).exclude(detail_id__in=updated_details).delete()

                        # Автоматически пересчитывается seat_count
                        agenda_instance.seat_count = QuestionDetail.objects.filter(question_id=agenda_instance).count()
                        agenda_instance.save()

                    # Удаление вопросов, которых нет в новом списке
                    Agenda.objects.filter(meeting=meeting).exclude(question_id__in=updated_agenda_ids).delete()

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_200_OK)
        
    # Отправка сообщения (собрания, меняется is_draft на false и сохраняется дата отправки)
    @action(detail=True, methods=['put'], url_path='send', permission_classes=[permissions.IsAdminUser])
    def send_meeting(self, request, pk=None):
        meeting = get_object_or_404(Main, pk=pk)

        # Проверка не отправлено ли сообщение ранее 
        if not meeting.is_draft:
            return Response({"error": "Сообщение уже отправлено."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на обязательные поля и наличие повестки дня
        required_fields = [
            'issuer', 'meeting_location', 'meeting_date', 'decision_date',
            'record_date', 'checkin', 'closeout', 'meeting_open',
            'meeting_close', 'deadline_date'
        ]
        missing_fields = [field for field in required_fields if not getattr(meeting, field, None)]

        if missing_fields:
            return Response({
                "error": f"Нельзя отправить сообщение, не заполнены обязательные поля: {', '.join(missing_fields)}"}, 
                status=status.HTTP_400_BAD_REQUEST)

        if not Agenda.objects.filter(meeting=meeting).exists():
            return Response({"error": "Нельзя отправить сообщение без повестки дня."}, status=status.HTTP_400_BAD_REQUEST)

        # Обновление статуса (больше не черновик)
        meeting.set_ready()

        return Response({
            "message": "Сообщение успешно отправлено!",
            "meeting_id": meeting.meeting_id,
            "is_draft": meeting.is_draft
        }, status=status.HTTP_200_OK)
    
    # Создание собрания
    @action(detail=False, methods=['post'], url_path='create', permission_classes=[permissions.IsAdminUser])
    def create_meeting(self, request):
        serializer = MeetingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Для пользователя список собраний, в которых он может участвовать 
    def list(self, request, *args, **kwargs):
        meetings = self.get_queryset()
        serialized_meetings = MeetingListSerializer(meetings, many=True).data
        return Response(serialized_meetings)

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
