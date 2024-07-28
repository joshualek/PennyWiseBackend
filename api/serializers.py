from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Budget, Expense, Income, Category, Goal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class BudgetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Budget
        fields = ["id", "user", "name", "amount", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

class ExpenseSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Expense
        fields = ["id", "budget", "name", "amount", "created_at", "category"]
        read_only_fields = ["id", "created_at"]
    
    def create(self, validated_data):
        # Ensure the budget belongs to the authenticated user
        budget = validated_data.get('budget')
        request = self.context.get('request')
        if budget.user != request.user:
            raise serializers.ValidationError("This budget does not belong to the authenticated user.")
        return super().create(validated_data)

class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ["id", "name", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['id', 'name', 'target_amount', 'current_amount', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_amount', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        return Goal.objects.create(user=request.user, **validated_data)