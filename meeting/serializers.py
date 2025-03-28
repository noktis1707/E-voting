from rest_framework import serializers
from .models import Main, QuestionDetail, Agenda, Issuer, DjangoRelation, VoteCount, VotingResult
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class IssuerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issuer
        fields = ['short_name', 'address']

class IssuerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issuer
        fields = ['issuer_id', 'full_name']

class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionDetail
        fields = ['detail_id','detail_text']

class AgendaSerializer(serializers.ModelSerializer):
    details = QuestionDetailSerializer(many=True, required=False)
    seat_count = serializers.IntegerField(required=False) 

    class Meta:
        model = Agenda
        fields = ['question_id', 'question','decision', 'single_vote_per_shareholder',
                  'cumulative', 'seat_count', 'details']

    def to_internal_value(self, data):
        details_data = data.get('details', [])
        validated_data = super().to_internal_value(data)
        validated_data['details'] = details_data  
        return validated_data

class MeetingCreateUpdateSerializer(serializers.ModelSerializer):
    meeting_url = serializers.ReadOnlyField()
    agenda = AgendaSerializer(many=True)
    class Meta:
        model = Main
        fields = [ 
                'meeting_id', 'meeting_name', 'issuer', 'meeting_location', 'meeting_date', 'decision_date',
                'deadline_date', 'checkin', 'closeout', 'meeting_open', 'meeting_close', 'vote_counting', 
                'first_or_repeated', 'record_date', 'annual_or_unscheduled', 'inter_or_extra_mural',
                'early_registration', 'meeting_url', 'status', 'agenda'
            ]
    
    def create(self, validated_data):
        issuer = validated_data.get('issuer')
        meeting_name = validated_data.get('meeting_name')
        validated_data['meeting_name'] = issuer.full_name if not meeting_name else meeting_name
        agenda_data = validated_data.pop('agenda', [])
        meeting = Main.objects.create(**validated_data)

        for agenda_item in agenda_data:
            details_data = agenda_item.pop('details', [])
            is_cumulative = agenda_item.get('cumulative', False)

            # Устанавливаем seat_count перед созданием Agenda
            agenda_item['seat_count'] = len(details_data) 

            # Создание записи повестки дня
            agenda = Agenda.objects.create(meeting=meeting, **agenda_item)

            # Создание подвопроса только для кумулятивных вопросов
            if is_cumulative and details_data:
                for detail in details_data:
                    QuestionDetail.objects.create(question_id=agenda, meeting_id=meeting, **detail)
            elif not is_cumulative and details_data:
                agenda.single_vote_per_shareholder = True
                for detail in details_data:
                    QuestionDetail.objects.create(question_id=agenda, meeting_id=meeting, **detail)
        return meeting


class MeetingSerializer(serializers.ModelSerializer):
    meeting_url = serializers.ReadOnlyField()
    agenda = AgendaSerializer(many=True)
    issuer = IssuerListSerializer()

    class Meta:
        model = Main
        # fields = '__all__'  # Отдаем все поля
        fields = [ 
            'meeting_id', 'meeting_name', 'issuer', 'meeting_location', 'meeting_date', 'decision_date',
            'deadline_date', 'checkin', 'closeout', 'meeting_open', 'meeting_close', 'vote_counting', 
            'first_or_repeated', 'record_date', 'annual_or_unscheduled', 'inter_or_extra_mural',
            'early_registration', 'meeting_url', 'status', 'agenda'
        ]

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'avatar']

class IssuerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issuer
        fields = ['short_name']
    
class MeetingListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    issuer = IssuerSerializer()
    class Meta:
        model = Main
        fields = ['meeting_id', 'issuer', 'meeting_date', 'status', 'is_draft', 'first_or_repeated',
                  'annual_or_unscheduled', 'updated_at', 'created_by', 'sent_at']
    
# class VoteCountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VoteCount
#         fields = ['account_id', 'account_fullname', 'json_quantity']
    
# class RegisteredUserWithAccountsSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(source="user.id")
#     full_name = serializers.CharField(source="user.full_name")
#     email = serializers.EmailField(source="user.email")

#     class Meta:
#         model = DjangoRelation
#         fields = ["user_id", "full_name", "email", "account_id"]

# class VotingResultSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VotingResult
#         fields = ['meeting_id', 'account_id', 'user_id', 'json_result']

# Добавление флага is_staff 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Добавляем флаг администратора в ответ
        data['is_staff'] = self.user.is_staff
        return data
    
class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])  # Декодируем токен
            data = super().validate(attrs)  # Получаем новый access-токен
            
            # Получаем пользователя
            user = User.objects.get(id=refresh["user_id"])
            data["is_staff"] = user.is_staff  # Добавляем is_staff

            return data
        except TokenError as e:
            raise InvalidToken(str(e))
        except User.DoesNotExist:
            raise InvalidToken("User not found")