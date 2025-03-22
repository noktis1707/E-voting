from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Issuer(models.Model):
    issuer_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=96)
    address = models.CharField(max_length=256)
    zip = models.IntegerField()
    ogrn = models.CharField(max_length=13)

    class Meta:
        db_table = 'meeting_issuer'

class Registrar(models.Model):
    registrar_id = models.AutoField(primary_key=True)
    registrar_name = models.CharField(max_length=300)
    address = models.CharField(max_length=256)
    zipcode = models.IntegerField()
    ogrn = models.CharField(max_length=13)

    class Meta:
        db_table = 'meeting_registrar'

class Main(models.Model):
    STATUS_CHOICES = [
        (1, 'Ожидается'),
        (2, 'Разрешена регистрация'),
        (3, 'Разрешено голосование'),
        (4, 'Голосование завершено'),
        (5, 'Собрание завершилось')
    ]

    meeting_id = models.AutoField(primary_key=True)     # номер в базе Meeting
    meeting_name = models.CharField(max_length=100, blank=True, null=True)      # описание собрания
    issuer = models.ForeignKey(Issuer, models.DO_NOTHING, blank=True, null=True)    # код эмитента
    meeting_location = models.CharField(max_length=200, blank=True, null=True)      # Место проведения \ почтовый адрес для направления бюллетеней
    meeting_date = models.DateField(blank=True, null=True)      # Дата собрания
    decision_date = models.DateField(blank=True, null=True)     # Дата принятия решения о созыве ОСА
    annual_or_unscheduled = models.BooleanField()               # Вид собрания (годовое или внеочередное) True - годовое, False - внеочередное
    first_or_repeated = models.BooleanField(blank=True, null=True)  # повторное или нет True - повторное, False - первичное
    inter_or_extra_mural = models.BooleanField()                # очное/заочное True - очное, False - заочное
    record_date = models.DateField(blank=True, null=True)       # Дата составления списка
    checkin = models.DateTimeField(blank=True, null=True)       # Начало регистрации (время)
    closeout = models.DateTimeField(blank=True, null=True)      # Окончание регистрации
    meeting_open = models.DateTimeField(blank=True, null=True)  # Начало собрания
    meeting_close = models.DateTimeField(blank=True, null=True) # Окончание собрания
    early_registration = models.BooleanField(blank=True, null=True) # досрочная регистрация
    deadline_date = models.DateField(blank=True, null=True)     # Дата окончания приема бюллетеней
    vote_counting = models.DateTimeField(blank=True, null=True) # Начало подсчета голосов
    meeting_url = models.CharField(max_length=100, blank=True, null=True) # ссылка на трансляцию
    registrar = models.ForeignKey(Registrar, models.DO_NOTHING, blank=True, null=True) #  код регистратора (ЦО, Тюмень и т.д.)
    protocol_date = models.DateField(blank=True, null=True)     # Дата составления протокола
    status = models.IntegerField(blank=True, null=True, choices=STATUS_CHOICES, default='1') # статус собрания (Ожидается, Разрешена регистрация, Разрешено голосование, Голосование завершено, Собрание завершилось)  

    is_draft = models.BooleanField(default = True) # Черновик ли он 
    created_at = models.DateField(auto_now_add=True) # Дата создания
    updated_at = models.DateField(auto_now=True, blank=True, null=True) # Дата последнего изменения
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True) # Кто создал (email)
    sent_at = models.DateField(blank=True, null=True) # Дата отправления

    def update_status(self):
        now = timezone.now()

        if self.meeting_close and now >= self.meeting_close:
            self.status = 5  # Собрание завершилось
        elif self.vote_counting and now >= self.vote_counting:
            self.status = 4  # Голосование завершено
        elif self.meeting_open and now >= self.meeting_open:
            self.status = 3  # Разрешено голосование
        elif self.checkin and now >= self.checkin:
            self.status = 2  # Разрешена регистрация
        else:
            self.status = 1  # Ожидается

    def set_ready(self):
        self.is_draft = False
        self.sent_at = timezone.now()
        self.save()

    def allowed_voting(self):
        return self.status == 3 
    



    # def is_fully_filled(self):
    #     required_fields = ['issuer', 'meeting_location', 'meeting_date', 'decision_date', 'annual_or_unscheduled', 
    #                        'inter_or_extra_mural', 'record_date', 'checkin', 'closeout', 'meeting_open', 
    #                        'meeting_close', 'early_registration', 'deadline_date']
    #     all_fields_filled = all(getattr(self, field) for field in required_fields)
    #     has_agenda = Agenda.objects.filter(meeting=self).exists()
    #     return all_fields_filled and has_agenda # Есть ли хотя бы один вопрос в повестке дня

    class Meta:
        db_table = 'meeting_main'

class Agenda(models.Model):
    question_id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(Main, on_delete=models.CASCADE, related_name='agenda')
    single_vote_per_shareholder = models.BooleanField(default=False)
    interest = models.BooleanField(default=False)
    question = models.TextField()
    decision = models.TextField()
    cumulative = models.BooleanField()
    seat_count = models.IntegerField()

    class Meta:
        db_table = 'meeting_agenda'
        unique_together = (('meeting', 'question_id'),)

class QuestionDetail(models.Model):
    question_id = models.ForeignKey(Agenda, on_delete=models.CASCADE, related_name='details')
    meeting_id = models.ForeignKey(Main, on_delete=models.CASCADE)
    detail_id = models.AutoField(primary_key=True)
    detail_text = models.TextField()

    class Meta:
        db_table = 'meeting_question_detail'
        unique_together = (('meeting_id', 'question_id', 'detail_id'),)


class VoteCount(models.Model):
    vote_count_id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(Main, on_delete=models.CASCADE)
    account_id = models.IntegerField()
    account_fullname = models.CharField(max_length=300)
    json_quantity = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'meeting_vote_count'
        unique_together = (('meeting', 'account_id'),)


class VotingResult(models.Model):
    voting_result_id = models.AutoField(primary_key=True)
    meeting_id = models.ForeignKey(Main, on_delete=models.CASCADE)
    account_id = models.IntegerField()
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    json_result = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'meeting_voting_result'
        unique_together = (('meeting_id', 'account_id', 'user_id'),)

class DjangoRelation(models.Model):
    vote_count = models.ForeignKey(VoteCount, on_delete=models.CASCADE)
    voting_result = models.ForeignKey(VotingResult, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Main, on_delete=models.CASCADE)
    account_id = models.IntegerField()
    registered = models.BooleanField(default=False)

    class Meta:
        db_table = 'meeting_django_relation'
        unique_together = (('meeting', 'account_id', 'user'),)

class Docs(models.Model):
    meeting = models.ForeignKey(Main, on_delete=models.CASCADE) 
    id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=200, blank=True, null=True)
    is_result = models.BooleanField(blank=True, null=True, default=False)
    url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'meeting_docs'
        unique_together = (('meeting', 'id'),)

class UserLink(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    key = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'meeting_user_link'

