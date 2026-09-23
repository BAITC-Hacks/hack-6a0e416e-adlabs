from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import ActivityHistory, EmployeeQuest, XPTransaction

class Command(BaseCommand):
    help = "Remove only demo quest actions; imported dataset remains intact"

    @transaction.atomic
    def handle(self, *args, **options):
        XPTransaction.objects.all().delete()
        EmployeeQuest.objects.all().delete()
        ActivityHistory.objects.filter(external_id__startswith="DEMO-").delete()
        self.stdout.write(self.style.SUCCESS("Demo progress reset"))
