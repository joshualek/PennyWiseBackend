from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Budget, Expense

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "user", "name", "amount", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "budget", "name", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]
    
    def create(self, validated_data):
        # Ensure the budget belongs to the authenticated user
        budget = validated_data.get('budget')
        request = self.context.get('request')
        if budget.user != request.user:
            raise serializers.ValidationError("This budget does not belong to the authenticated user.")
        return super().create(validated_data)