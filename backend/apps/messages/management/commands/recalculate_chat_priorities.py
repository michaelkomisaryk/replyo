from django.core.management.base import BaseCommand

from apps.messages.priority import recalculate_all_priorities


class Command(BaseCommand):
    help = "Recalculate chat priorities based on messages and orders."

    def handle(self, *args, **options):
        updated = recalculate_all_priorities()
        self.stdout.write(
            self.style.SUCCESS(f"Recalculated priorities for {updated} chat(s).")
        )
