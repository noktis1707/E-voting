from rest_framework import serializers
from .models import Main, QuestionDetail, Agenda

class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionDetail
        fields = ['detail_id','detail_text']

class AgendaSerializer(serializers.ModelSerializer):
    details = QuestionDetailSerializer(many=True, source='detail')
    seat_count = serializers.IntegerField(required=False)

    class Meta:
        model = Agenda
        fields = ['question_id', 'question','decision', 'cumulative', 'seat_count', 'details']

    def create(self, validated_data):
        details_data = validated_data.pop('details', []) if 'details' in validated_data else []
        is_cumulative = validated_data.get('cumulative', False)

        # Устанавливаем seat_count в зависимости от количества подвопросов, если нет, то 1
        seat_count = len(details_data) if is_cumulative else 1
        validated_data['seat_count'] = seat_count  

        # Создаем пункт повестки дня
        agenda = Agenda.objects.create(**validated_data)
        
        # Создаём подвопросы, если они есть
        for detail in details_data:
            QuestionDetail.objects.create(question_id=agenda, meeting_id=agenda.meeting, **detail)


        return agenda

class MeetingSerializer(serializers.ModelSerializer):
    meeting_url = serializers.ReadOnlyField()
    agenda = AgendaSerializer(many=True)

    class Meta:
        model = Main
        fields = '__all__'  # Отдаем все поля
        # fields = [ 
        #     'meeting_name', 'issuer', 'location', 'meeting_date', 'decision_date',
        #     'protocol_date', 'deadline_date', 'checkin_time', 'closeout_time', 'meeting_open_time', 
        #     'meeting_close_time', 'vote_counting', 'first_or_repeated', 'record_date', 'type', 'form',
        #     'early_registration', 'registrar', 'status'
        # ]
    
    def create(self, validated_data):
        #  meeting = Main.objects.create(**validated_data)
        agenda_data = validated_data.pop('agenda')
        meeting = Main.objects.create(**validated_data)

        for agenda_item in agenda_data:
            details_data = agenda_item.pop('details', []) if 'details' in agenda_item else []
            is_cumulative = agenda_item.get('cumulative', False)

            # Устанавливаем seat_count перед созданием Agenda
            agenda_item['seat_count'] = len(details_data) if is_cumulative else 1

            # Создание записи повестки дня
            agenda = Agenda.objects.create(meeting=meeting, **agenda_item)

            # Создани подвопросоа только для кумулятивных вопросов
            if is_cumulative and details_data:
                for detail in details_data:
                    QuestionDetail.objects.create(question_id=agenda, meeting_id=meeting, **detail)
                agenda.seat_count = len(details_data)  # Устанавливаем seat_count как число подвопросов
            else:
                agenda.seat_count = 1  # Если не кумулятивный, устанавливаем 1

            agenda.save() 

        return meeting