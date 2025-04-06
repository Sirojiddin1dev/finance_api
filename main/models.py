from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _



class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

    # Balans maydonlari
    php_invest_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    php_reit_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.phone_number

    @property
    def total_balance(self):
        return self.php_invest_balance + self.php_reit_balance

    def get_formatted_balance(self, balance_type=None):
        if balance_type == 'php_invest':
            return "${:,.2f}".format(self.php_invest_balance)
        elif balance_type == 'php_reit':
            return "${:,.2f}".format(self.php_reit_balance)
        else:
            return "${:,.2f}".format(self.total_balance)


class BalanceAdjustmentLog(models.Model):
    """Admin tomonidan qilingan o'zgarishlar tarixi"""
    FUND_TYPES = (
        ('php_invest', 'PHP Invest Total'),
        ('php_reit', 'PHP REIT Fund Total'),
    )

    ADJUSTMENT_TYPES = (
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
    )

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='balance_adjustments')
    fund_type = models.CharField(max_length=20, choices=FUND_TYPES)
    percentage = models.DecimalField(max_digits=6, decimal_places=2)
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    affected_users_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        action = "increased" if self.adjustment_type == "increase" else "decreased"
        return f"{self.get_fund_type_display()} {action} by {self.percentage}% on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# class PaymentCard(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
#     card_number = models.CharField(
#         max_length=19,
#         validators=[
#             RegexValidator(
#                 regex=r'^\d{4} \d{4} \d{4} \d{4}$',
#                 message='Karta raqami 16 ta raqamdan iborat bo\'lishi kerak'
#             )
#         ]
#     )
#     expiry_date = models.CharField(
#         max_length=5,
#         validators=[
#             RegexValidator(
#                 regex=r'^(0[1-9]|1[0-2])/\d{2}$',
#                 message='Yaroqlilik muddati MM/YY formatida bo\'lishi kerak'
#             )
#         ]
#     )
#     is_main = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         verbose_name = "To'lov kartasi"
#         verbose_name_plural = "To'lov kartalari"
#
#     def __str__(self):
#         return f"{self.card_number} ({self.user.username})"


class DailyTransaction(models.Model):
    CATEGORY = (
        ("income", "income"),
        ("expense", "expense")
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_transactions')
    category = models.CharField(max_length=255, choices=CATEGORY)
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kunlik tranzaksiya"
        verbose_name_plural = "Kunlik tranzaksiyalar"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount}"


# class Investment(models.Model):
#     INVESTMENT_TYPES = (
#         ('reit', 'REIT Fond'),
#         ('stock', 'Aksiya'),
#         ('bond', 'Obligatsiya'),
#         ('other', 'Boshqa'),
#     )
#
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
#     type = models.CharField(max_length=20, choices=INVESTMENT_TYPES)
#     card = models.ForeignKey(PaymentCard, on_delete=models.SET_NULL, null=True)
#     amount = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         validators=[MinValueValidator(0)]
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=[
#             ('pending', 'Kutilmoqda'),
#             ('completed', 'Muvaffaqiyatli'),
#             ('failed', 'Muvaffaqiyatsiz'),
#         ],
#         default='pending'
#     )
#     description = models.TextField(null=True, blank=True)
#     date = models.DateField(default=timezone.now)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         verbose_name = "Investitsiya"
#         verbose_name_plural = "Investitsiyalar"
#         ordering = ['-date', '-created_at']
#
#     def __str__(self):
#         return f"{self.user.username} - {self.get_type_display()} - {self.amount}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    push_notifications = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    img = models.ImageField(upload_to='notification/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class About(models.Model):
    text = models.TextField(_("Matnni kiriting"))

    def __str__(self):
        return self.title


class Help(models.Model):
    telegram = models.CharField(_("Aloqa markazi"), max_length=500)
    call = models.CharField(_("Aloqa markazi"), max_length=13)

    def __str__(self):
        return self.telegram


class Video(models.Model):
    video = models.CharField(_("Video urlini kiriting"),max_length=50)
    title = models.CharField(_("Sarlavhani kiriting"),max_length = 100, blank=False)
    description = models.CharField(_("Qisqacha fikringizni kiriting"),max_length = 255, blank=False)

    def __str__(self):
        return self.title
