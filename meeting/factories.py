import re
import factory
import random
from faker import Faker
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from .models import Main, Issuer, Registrar

User = get_user_model()

fake = Faker("ru_RU") 

class IssuerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Issuer

    # company_name = factory.LazyAttribute(lambda _: fake.company())
    # full_name = factory.LazyAttribute(lambda obj: f"Акционерное общество {obj.company_name}")
    # short_name = factory.LazyAttribute(lambda obj: f"АО {obj.company_name}")
    @factory.lazy_attribute
    def full_name(self):
        company_name = fake.company()
        # company_name = re.sub(r"\s*(ООО|ОАО|ЗАО|ИП|АО)\s*$", "", company_name)
        company_name = re.sub(r"^(ООО|ОАО|ЗАО|ИП|АО|РАО|НПО)\s+", "", company_name)
        return f"Акционерное общество {company_name}"

    @factory.lazy_attribute
    def short_name(self):
        return f"АО {self.full_name.split(' ', 2)[-1]}"
    
    address = factory.LazyAttribute(lambda _: fake.address())
    zip = factory.LazyFunction(lambda: random.randint(100000, 199999)) 
    ogrn = factory.LazyAttribute(lambda _: str(random.randint(1000000000000, 9999999999999))) 
# class RegistrarFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Registrar

#     registrar_name = factory.LazyAttribute(lambda _: fake.company() + " Регистратор")
#     address = factory.LazyAttribute(lambda _: fake.address())
#     zipcode = factory.LazyAttribute(lambda _: fake.random_int(min=100000, max=199999))
#     ogrn = factory.LazyAttribute(lambda _: str(fake.random_int(min=1000000000000, max=9999999999999)))

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.phone_number())
    email = factory.LazyAttribute(lambda _: fake.email())
    is_staff = False  # По умолчанию не админ

class MainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Main

    issuer = factory.SubFactory(IssuerFactory)
    meeting_name = IssuerFactory.full_name
    # registrar = factory.SubFactory(RegistrarFactory)
    # created_by = factory.SubFactory(UserFactory)
    @factory.lazy_attribute
    def created_by(self):
        admin, _ = User.objects.get_or_create(username="admin1", defaults={"is_staff": True, "is_superuser": True})
        return admin
    
    meeting_location = factory.LazyAttribute(lambda _: fake.address())

    # Даты собрания (логика проверки, чтобы даты были корректными)
    meeting_date = factory.LazyFunction(lambda: now().date() + timedelta(days=random.randint(1, 30)))
    decision_date = factory.LazyAttribute(lambda obj: obj.meeting_date - timedelta(days=random.randint(5, 10)))
    record_date = factory.LazyAttribute(lambda obj: obj.meeting_date - timedelta(days=random.randint(10, 15)))
    deadline_date = factory.LazyAttribute(lambda obj: obj.meeting_date - timedelta(days=random.randint(1, 5)))

    checkin = factory.LazyAttribute(lambda obj: now() + timedelta(days=1, hours=random.randint(8, 10)))
    closeout = factory.LazyAttribute(lambda obj: obj.checkin + timedelta(hours=random.randint(1, 3)))
    meeting_open = factory.LazyAttribute(lambda obj: obj.closeout + timedelta(hours=1))
    meeting_close = factory.LazyAttribute(lambda obj: obj.meeting_open + timedelta(hours=random.randint(1, 5)))

    vote_counting = factory.LazyAttribute(lambda obj: obj.meeting_close + timedelta(hours=1))

    annual_or_unscheduled = factory.LazyAttribute(lambda _: random.choice([True, False]))
    first_or_repeated = factory.LazyAttribute(lambda _: random.choice([True, False]))
    inter_or_extra_mural = factory.LazyAttribute(lambda _: random.choice([True, False]))
    early_registration = factory.LazyAttribute(lambda _: random.choice([True, False]))

    meeting_url = factory.LazyAttribute(lambda _: fake.url())
    protocol_date = factory.LazyAttribute(lambda obj: obj.meeting_date + timedelta(days=random.randint(1, 3)))

