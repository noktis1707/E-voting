from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action
from django.db import transaction
from meeting.services.account_service import get_accounts

from meeting.permissions import IsAdminOrReadOnly
from meeting.models import Main, DjangoRelation, Agenda, QuestionDetail, VoteCount, Issuer
from meeting.serializers import MeetingSerializer, MeetingListSerializer, IssuerInfoSerializer, MeetingCreateUpdateSerializer
# Собрания
class MeetingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'drafts']:
            return MeetingListSerializer  # Для списка собраний
        return MeetingSerializer  # Для детального просмотра

    def get_queryset(self):
        user = self.request.user
        meetings = Main.objects.all()

        # Обновление статуса только для собраний, которые НЕ являются черновиками
        for meeting in meetings:
            meeting.update_status()

        # Для администратора список всех собраний, которые не являются черновиками
        if user.is_staff:
            return meetings.filter(is_draft=False) 
            # return Main.objects.all() 
        
        # Для участника список собраний, в которых он может участвовать и которые не являются черновиками
        meeting_ids = DjangoRelation.objects.filter(user=user).values_list('meeting_id', flat=True)
        return meetings.filter(meeting_id__in=meeting_ids, is_draft=False)
    
    def update(self, request, *args, **kwargs):
        """Запрещаем редактирование отправленных собраний"""
        meeting = self.get_object()
        if not meeting.is_draft:
            return Response({"error": "Редактирование отправленного собрания запрещено."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Запрещаем частичное обновление отправленных собраний"""
        meeting = self.get_object()
        if not meeting.is_draft:
            return Response({"error": "Редактирование отправленного собрания запрещено."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    # Черновики все (только админ)
    @action(detail=False, methods=['get'], url_path='drafts', permission_classes=[permissions.IsAdminUser])
    def drafts(self, request):
        """Список всех черновиков"""
        drafts = Main.objects.filter(is_draft=True)
        serializer = MeetingListSerializer(drafts, many=True)
        return Response(serializer.data)
    
    # Конкретный черновик (только админ) для возможного редактирования
    @action(detail=True, methods=['get', 'put'], url_path='draft', permission_classes=[permissions.IsAdminUser])
    def draft_detail(self, request, pk=None):
        """Конкретный черновик"""
        meeting = Main.objects.get(pk=pk)

        if not meeting.is_draft:
            return Response({"error": "Это не черновик."}, status=status.HTTP_400_BAD_REQUEST)

        # Вернуть заполненные данные черновика
        if request.method == 'GET':
            serializer = MeetingCreateUpdateSerializer(meeting)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Обновление данных черновика
        if request.method in ['PUT']:
            meeting_data = request.data.copy()
            agenda_data = meeting_data.pop('agenda', [])

            required_fields = {
                'meeting_id', 'meeting_name', 'issuer', 'meeting_location', 'meeting_date', 'decision_date',
                'deadline_date', 'checkin', 'closeout', 'meeting_open', 'meeting_close', 'vote_counting', 
                'first_or_repeated', 'record_date', 'annual_or_unscheduled', 'inter_or_extra_mural',
                'early_registration', 'meeting_url', 'status'
            }
            missing_fields = required_fields - set(meeting_data.keys())

            if missing_fields:
                return Response({"error": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Обновление данных собрания
            serializer = MeetingCreateUpdateSerializer(meeting, data=meeting_data, partial=True)

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
        """Отправка сообщения, проверяется все ли поля заполнены"""
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
    @action(detail=False, methods=['get','post'], url_path='create', permission_classes=[permissions.IsAdminUser])
    def create_meeting(self, request):
        """Создание собрания"""
        # Получение списка эмитентов при создании собрания
        if request.method == 'GET':
            issuer = Issuer.objects.all()
            serializer = IssuerInfoSerializer(issuer, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        if request.method == 'POST':
            serializer = MeetingCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=self.request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Для пользователя список собраний, в которых он может участвовать 
    def list(self, request, *args, **kwargs):
        meetings = self.get_queryset()
        serialized_meetings = MeetingListSerializer(meetings, many=True).data
        return Response(serialized_meetings)
    
    # Добавить информацию о регистрации для участника собрания
    def retrieve(self, request, pk=None):
        """Получение конкретного собрания"""
        meeting = get_object_or_404(Main, pk=pk)
        user = request.user
        serializer = MeetingSerializer(meeting)

        response_data = serializer.data

        if not user.is_staff:
            # Проверка, что у пользователя есть лицевые счета для голосования
            user_accounts = get_accounts(meeting, user)
            if not user_accounts:
                return Response({"error": "У вас нет прав для голосования в этом собрании."}, status=status.HTTP_403_FORBIDDEN)

            is_registered = DjangoRelation.objects.filter(user=user, meeting=meeting, registered=True).exists()
            response_data["is_registered"] = is_registered

        return Response(response_data)
    
    # Получение списка account_id для пользователя    
    @action(detail=True, methods=['get'], url_path='accounts')
    def get_user_accounts(self, request, pk=None):
        """Получить список лицевых счетов по собранию"""
        meeting = get_object_or_404(Main, pk=pk)
        user = request.user

        accounts = get_accounts(meeting, user)

        if not accounts:
            return Response({"error": "У вас нет прав для голосования в этом собрании."}, status=status.HTTP_403_FORBIDDEN)


        return Response({"meeting_id": pk, "accounts": accounts}, status=status.HTTP_200_OK)
    