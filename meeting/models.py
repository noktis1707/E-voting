from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Issuer(models.Model):
    issuer_id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=96)
    address = models.CharField(max_length=256)
    zip = models.IntegerField()
    ogrn = models.CharField(max_length=13)

    class Meta:
        db_table = 'meeting_issuer'

class Registrar(models.Model):
    registrar_id = models.IntegerField(primary_key=True)
    registrar_name = models.CharField(max_length=300)
    address = models.CharField(max_length=256)
    zipcode = models.IntegerField()
    ogrn = models.CharField(max_length=13)

    class Meta:
        db_table = 'meeting_registrar'

class Main(models.Model):
    meeting_id = models.IntegerField(primary_key=True)
    meeting_name = models.CharField(max_length=100, blank=True, null=True)
    issuer = models.ForeignKey(Issuer, models.DO_NOTHING, blank=True, null=True)
    meeting_location = models.CharField(max_length=200, blank=True, null=True)
    meeting_date = models.DateField(blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)
    protocol_date = models.DateField(blank=True, null=True)
    deadline_date = models.DateField(blank=True, null=True)
    checkin = models.DateTimeField(blank=True, null=True)
    closeout = models.DateTimeField(blank=True, null=True)
    meeting_open = models.DateTimeField(blank=True, null=True)
    meeting_close = models.DateTimeField(blank=True, null=True)
    vote_counting = models.DateTimeField(blank=True, null=True)
    annual_or_unscheduled = models.BooleanField()
    first_or_repeated = models.BooleanField()
    record_date = models.DateField(blank=True, null=True)
    early_registration = models.BooleanField()
    meeting_url = models.CharField(max_length=100, blank=True, null=True)
    inter_or_extra_mural = models.BooleanField()
    registrar = models.ForeignKey(Registrar, models.DO_NOTHING, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'meeting_main'

class Agenda(models.Model):
    question_id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(Main, on_delete=models.CASCADE, related_name='agenda')
    single_vote_per_shareholder = models.BooleanField()
    interest = models.BooleanField()
    question = models.TextField()
    decision = models.TextField()
    cumulative = models.BooleanField()
    seat_count = models.IntegerField()

    class Meta:
        db_table = 'meeting_agenda'
        unique_together = (('meeting', 'question_id'),)

class QuestionDetail(models.Model):
    question_id = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    meeting_id = models.IntegerField(Main, on_delete=models.CASCADE)
    detail_id = models.IntegerField()
    detail_text = models.TextField()

    class Meta:
        db_table = 'meeting_question_detail'
        unique_together = (('meeting_id', 'question_id', 'detail_id'),)

class UserLink(models.Model):
    user = models.OneToOneField(User, models.DO_NOTHING, primary_key=True)
    key = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'meeting_user_link'


class VoteCount(models.Model):
    vote_count_id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(Main, models.DO_NOTHING)
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
    vote_count = models.ForeignKey('VoteCount', models.DO_NOTHING)
    voting_result = models.ForeignKey('VotingResult', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    meeting = models.ForeignKey('Main', models.DO_NOTHING)
    account_id = models.IntegerField()
    registered = models.BooleanField(blank=True, null=True, default=False)

    class Meta:
        db_table = 'meeting_django_relation'
        unique_together = (('meeting', 'account_id', 'user'),)


class Docs(models.Model):
    meeting = models.OneToOneField(Main, on_delete=models.CASCADE)  # The composite primary key (meeting_id, id) found, that is not supported. The first column is selected.
    id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=200, blank=True, null=True)
    is_result = models.BooleanField(blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'meeting_docs'
        unique_together = (('meeting', 'id'),)