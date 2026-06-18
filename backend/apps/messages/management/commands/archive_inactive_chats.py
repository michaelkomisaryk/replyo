from django.core.management.base import BaseCommand

from apps.accounts.models import Shop
from apps.messages.visibility import archive_stale_chats


class Command(BaseCommand):
    help = "Archive inactive chats and completed-order chats past the visibility window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--shop-id",
            type=int,
            help="Limit archiving to a single shop.",
        )

    def handle(self, *args, **options):
        shop_id = options.get("shop_id")
        if shop_id:
            shop = Shop.objects.filter(id=shop_id).first()
            if not shop:
                self.stderr.write(self.style.ERROR(f"Shop {shop_id} not found."))
                return
            archived = archive_stale_chats(shop=shop)
            self.stdout.write(
                self.style.SUCCESS(f"Archived {archived} chat(s) for shop {shop_id}.")
            )
            return

        total = 0
        for shop in Shop.objects.all().iterator():
            total += archive_stale_chats(shop=shop)
        self.stdout.write(self.style.SUCCESS(f"Archived {total} chat(s) across all shops."))
