from meeting.models import DjangoRelation, VoteCount

# Лицевые счета пользователя для голосования 
def get_accounts(meeting, user):
      # Находим связи пользователя с собранием
      accounts = DjangoRelation.objects.filter(user=user, meeting=meeting).values("account_id")

      # Получить связанные данные из VoteCount (account_id и account_fullname)
      vote_counts = VoteCount.objects.filter(meeting=meeting, account_id__in=accounts)

      # Список словарей с account_id и account_fullname
      accounts_info = [{"account_id": vote_count.account_id, 
                        "account_fullname": vote_count.account_fullname} for vote_count in vote_counts]
      
      return accounts_info

# Проверка зарагестрирован ли пользователь в собрании
def registered(meeting, user):
      is_registered = DjangoRelation.objects.filter(user=user, 
                                                    meeting=meeting, registered=True).exists()
      return is_registered

      