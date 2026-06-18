from django.core.management.base import BaseCommand

from apps.integrations.inbound_sync import process_unhandled_webhook_events


class Command(BaseCommand):
    help = "Process unhandled Instagram webhook events (periodic sync fallback)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of queued webhook events to process.",
        )

    def handle(self, *args, **options):
        processed = process_unhandled_webhook_events(limit=options["limit"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {processed} Instagram webhook event(s)."
            )
        )
