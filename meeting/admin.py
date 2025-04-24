from django import forms
from django.contrib import admin

from .models import Main, Registrar, Issuer, Agenda, QuestionDetail, VoteCount, VotingResult, DjangoRelation

class MeetingAdmin(admin.ModelAdmin):
    list_display = [ 
            'meeting_name', 'meeting_id', 'meeting_date', 'status', 'created_at', 'updated_at', 'sent_at', 'is_draft'
        ]
    search_fields = ('issuer', 'registrar') 

class AgendaAdmin(admin.ModelAdmin):
    list_display = [ 
            'question', 'question_id', 'meeting', 'cumulative', 'seat_count'
        ]

class QuestionDetailAdmin(admin.ModelAdmin):
    list_display = [ 
            'detail_text', 'detail_id', 'question_id', 'meeting_id'
        ]

class DjangoRelationAdmin(admin.ModelAdmin):
    list_display = [ 
            'user', 'account_id', 'meeting', 'vote_count', 'voting_result', 'registered'
        ]
    
class VoteCountAdmin(admin.ModelAdmin):
    list_display = [ 
            'account_id', 'vote_count_id','account_fullname', 'meeting', 'json_quantity'
        ]
    
class VotingResultAdmin(admin.ModelAdmin):
    list_display = [ 
            'account_id', 'voting_result_id','user_id', 'meeting_id', 'json_result'
        ]
    
class RegistrarAdmin(admin.ModelAdmin):
    list_display = [ 
            'registrar_name', 'registrar_id'
        ]
    
class IssuerAdmin(admin.ModelAdmin):
    list_display = [ 
            'short_name', 'full_name', 'issuer_id'
        ]
    
admin.site.register(Main, MeetingAdmin)
# admin.site.register(Registrar)
# admin.site.register(Issuer)
admin.site.register(Agenda, AgendaAdmin)
admin.site.register(QuestionDetail, QuestionDetailAdmin)
admin.site.register(VoteCount, VoteCountAdmin)
admin.site.register(VotingResult, VotingResultAdmin)
admin.site.register(DjangoRelation, DjangoRelationAdmin)
admin.site.register(Registrar, RegistrarAdmin)
admin.site.register(Issuer, IssuerAdmin)

