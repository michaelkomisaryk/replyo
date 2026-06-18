from django.core.management.base import BaseCommand

from apps.accounts.models import Shop
from apps.messages.notifications import send_waiting_reply_reminders


class Command(BaseCommand):
    help = "Send in-app reminders for chats waiting longer than the reply threshold."

    def add_arguments(self, parser):
        parser.add_argument(
            "--shop-id",
            type=int,
            help="Limit reminders to a single shop.",
        )

    def handle(self, *args, **options):
        shop_id = options.get("shop_id")
        if shop_id:
            shop = Shop.objects.filter(id=shop_id).first()
            if not shop:
                self.stderr.write(self.style.ERROR(f"Shop {shop_id} not found."))
                return
            created = send_waiting_reply_reminders(shop=shop)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {created} waiting-reply reminder(s) for shop {shop_id}."
                )
            )
            return

        total = 0
        for shop in Shop.objects.all().iterator():
            total += send_waiting_reply_reminders(shop=shop)
        self.stdout.write(
            self.style.SUCCESS(f"Created {total} waiting-reply reminder(s) across all shops.")
        )
