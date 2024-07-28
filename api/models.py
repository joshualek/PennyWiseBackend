from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import re

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_goal_achieved(self):
        return self.current_amount >= self.target_amount

    def add_savings(self, amount):
        self.current_amount = models.F('current_amount') + amount
        self.save(update_fields=['current_amount'])

    def redeem(self):
        if self.is_goal_achieved():
            self.delete()





class StudentDiscount(models.Model):
    message_id = models.IntegerField(unique=True, default=0)
    channel_id = models.BigIntegerField(default=0)
    message = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    channel_link = models.URLField(blank=True, null=True)
    discount_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"StudentDiscount {self.message_id}"

    def save(self, *args, **kwargs):
        self.extract_links()
        super().save(*args, **kwargs)

    def extract_links(self):
        bitly_pattern = re.compile(r'bit\.ly/\S+')
        telegram_pattern = re.compile(r'https://t\.me/joinchat/\S+')
        remove_pattern = re.compile(r'👉.*')
        private_channel_pattern = re.compile(r'Private channel for students only: https://t\.me/joinchat/\S+')


        # Extract bit.ly link
        bitly_match = bitly_pattern.search(self.message)
        if bitly_match:
            self.discount_link = bitly_match.group(0)
        else:
            self.discount_link = ""

        # Extract Telegram link
        telegram_match = telegram_pattern.search(self.message)
        if telegram_match:
            self.channel_link = telegram_match.group(0)
        else:
            self.channel_link = None

        # Remove the private channel text
        self.message = private_channel_pattern.sub('', self.message).strip()

        # Remove the unwanted part of the message
        self.message = remove_pattern.sub('', self.message).strip()

    @staticmethod
    def load_messages_from_json():
        try:
            with open('api/telegram-scraper/channel_messages.json', 'r') as file:
                messages = json.load(file)

            for msg in messages:
                channel_id = msg.get('peer_id', {}).get('channel_id', 0)  # Default to 0 if not found
                date = msg.get('date', timezone.now())  # Use current time if date is not found
                student_discount = StudentDiscount(
                    message_id=msg.get('id', 0),  # Use 0 if id is not found
                    channel_id=channel_id,
                    message=msg.get('message', ''),  # Use empty string if message is not found
                    date=date,
                )
                student_discount.save()
        except FileNotFoundError:
            print("The file channel_messages.json was not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON from channel_messages.json.")