from django.core.management.base import BaseCommand, CommandError

from apps.integrations.dev_simulate import SimulateInboundError, simulate_inbound_dm


class Command(BaseCommand):
    help = (
        "Simulate an inbound Instagram DM in development (mock connection only). "
        "Use --username to choose the customer Instagram handle."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            "-u",
            required=True,
            help="Customer Instagram username (without @), e.g. beauty_buyer",
        )
        parser.add_argument(
            "--text",
            "-t",
            default="Hello from Instagram (dev simulation)",
            help="Message body text.",
        )
        parser.add_argument(
            "--shop",
            type=int,
            default=None,
            help="Shop ID (defaults to the first connected shop).",
        )
        parser.add_argument(
            "--sender-id",
            default=None,
            help="Optional Meta sender ID (defaults to mock_sender_<username>).",
        )

    def handle(self, *args, **options):
        try:
            message = simulate_inbound_dm(
                username=options["username"],
                text=options["text"],
                shop_id=options["shop"],
                sender_id=options["sender_id"],
            )
        except SimulateInboundError as exc:
            raise CommandError(exc.message) from exc

        client = message.chat.client
        self.stdout.write(
            self.style.SUCCESS(
                f"Created inbound DM from @{client.instagram_username} "
                f"in chat #{message.chat_id}: {message.content!r}"
            )
        )
