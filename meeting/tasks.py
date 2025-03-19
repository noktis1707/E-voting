# from celery import shared_task
# from .models import Main


# @shared_task
# def update_meeting_statuses():    
#     meetings = Main.objects.filter(status__lt=5)  # Берём только те, что еще не завершились

#     for meeting in meetings:
#         old_status = meeting.status
#         meeting.update_status()  # Проверяем новый статус
#         if meeting.status != old_status:  # Если статус изменился — сохраняем
#             meeting.save(update_fields=['status'])