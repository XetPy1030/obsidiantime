from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from obsidiantime.chat.models import Message
from obsidiantime.main.models import Quote, SiteSettings, SocialLink


class Command(BaseCommand):
    help = "Setup initial data for ObsidianTime"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up initial data..."))

        # Create superuser if it doesn't exist
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@obsidiantime.ru",
                password="admin123",
                first_name="Админ",
                last_name="ObsidianTime",
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created superuser: {admin.username}")
            )

        # Create demo user
        if not User.objects.filter(username="demo").exists():
            demo_user = User.objects.create_user(
                username="demo",
                email="demo@obsidiantime.ru",
                password="demo123",
                first_name="Демо",
                last_name="Пользователь",
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created demo user: {demo_user.username}")
            )

        # Create site settings
        settings, created = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                "site_title": "ObsidianTime",
                "site_description": "Место для мемов, общения и веселья!",
                "show_rickroll": True,
                # rickroll_video will be empty by default -
                # admin can upload file manually
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created site settings"))
            self.stdout.write(
                self.style.WARNING(
                    "Загрузите видео файл для рикролла через админку: /admin/"
                )
            )

        # Create social links
        social_links_data = [
            {
                "platform": "twitch",
                "title": "ObsidianTime на Twitch",
                "url": "https://twitch.tv/obsidiantime",
                "description": "Стримы и развлечения",
                "order": 1,
            },
            {
                "platform": "youtube",
                "title": "ObsidianTime на YouTube",
                "url": "https://youtube.com/@obsidiantime",
                "description": "Видео и обзоры",
                "order": 2,
            },
            {
                "platform": "telegram",
                "title": "ObsidianTime в Telegram",
                "url": "https://t.me/obsitgroup",
                "description": "Новости и обсуждения",
                "order": 3,
            },
        ]

        for link_data in social_links_data:
            link, created = SocialLink.objects.get_or_create(
                platform=link_data["platform"], defaults=link_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created social link: {link.title}")
                )

        # Create initial quotes
        quotes_data = [
            {
                "text": (
                    "Жизнь — это то, что происходит с тобой, пока ты строишь планы."
                ),
                "author": "Джон Леннон",
            },
            {
                "text": ("Будьте собой; все остальные роли уже заняты."),
                "author": "Оскар Уайльд",
            },
            {
                "text": (
                    "Единственный способ делать великую работу — "
                    "любить то, что ты делаешь."
                ),
                "author": "Стив Джобс",
            },
            {
                "text": "Ошибки — это доказательство того, что ты пытаешься.",
                "author": "Неизвестен",
            },
            {
                "text": (
                    "Программирование — это не наука. Программирование — это искусство."
                ),
                "author": "Дональд Кнут",
            },
        ]

        admin_user = User.objects.get(username="admin")
        for quote_data in quotes_data:
            quote, created = Quote.objects.get_or_create(
                text=quote_data["text"],
                defaults={"author": quote_data["author"], "added_by": admin_user},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created quote: {quote.text[:50]}...")
                )

        # Create welcome message
        welcome_message, created = Message.objects.get_or_create(
            content=(
                "Добро пожаловать в ObsidianTime! "
                "🚀 Здесь можно общаться, делиться мемами "
                "и просто весело проводить время!"
            ),
            defaults={"author": admin_user, "message_type": "text"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created welcome message"))

        self.stdout.write(self.style.SUCCESS("Successfully set up initial data!"))
        self.stdout.write(self.style.WARNING("Admin credentials: admin / admin123"))
        self.stdout.write(self.style.WARNING("Demo user credentials: demo / demo123"))
