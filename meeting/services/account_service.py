from meeting.models import DjangoRelation, VoteCount, VotingResult

# Лицевые счета пользователя для голосования 
def get_accounts(meeting, user):
      # Находим связи пользователя с собранием
      relations = DjangoRelation.objects.filter(user=user, meeting=meeting)

      accounts_info = []

      for relation in relations:
            account_id = relation.account_id

            # Получаем ФИО из VoteCount
            vote_count = VoteCount.objects.filter(meeting=meeting, account_id=account_id).first()
            account_fullname = vote_count.account_fullname if vote_count else "—"

            # Проверяем, голосовал ли пользователь
            has_voted = VotingResult.objects.filter(
                  meeting_id=meeting,
                  account_id=account_id,
                  user_id=user,
                  json_result__isnull=False
            ).exists()

            accounts_info.append({
                  "account_id": account_id,
                  "account_fullname": account_fullname,
                  "has_voted": has_voted
            })
            
      return accounts_info

# Проверка зарагестрирован ли пользователь в собрании
def registered(meeting, user):
      is_registered = DjangoRelation.objects.filter(user=user, 
                                                    meeting=meeting, registered=True).exists()
      return is_registered

# Проверка принадлежит ли лицевой счет пользователю
def has_account(meeting, user, account_id):
    return DjangoRelation.objects.filter(
        meeting=meeting,
        user=user,
        account_id=account_id,
        registered=True
    ).exists()

      