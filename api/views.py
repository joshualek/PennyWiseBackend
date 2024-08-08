
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Avg, F, OuterRef, Subquery,IntegerField,Case,When
from django.db.models.functions import ExtractMonth, ExtractYear, ExtractWeek, Coalesce
from django.utils.timezone import now
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from .serializers import UserSerializer, BudgetSerializer, ExpenseSerializer, IncomeSerializer, CategorySerializer, StudentDiscountSerializer, GoalSerializer
from .models import Budget, Expense, Income, Category, StudentDiscount, Goal
from openpyxl import Workbook
from django.http import HttpResponse
from rest_framework.views import APIView


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

# Create a viewset for a single budget on BudgetPage.jsx
class BudgetDetailView(generics.RetrieveAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        budget = Budget.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()
        if not budget:
            raise NotFound("Budget not found")
        return budget

# Create a viewset for all budgets  
class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    # override get_queryset() to return only budgets for the authenticated user
    def get_queryset(self):
        userName = self.request.user #.request allows you to access to request object that allows you to specify the user
        return Budget.objects.filter(user=userName) 

    # override perform_create() to add the budget to the user
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(user=self.request.user) # have to manually pass in the user, cause it is a read-only field
        else: 
            print(serializer.errors)

class BudgetDeleteView(generics.DestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        userName = self.request.user
        return Budget.objects.filter(user=userName) 

# Create a filtered viewset for expenses on BudgetPage.jsx
# This viewset is beneficial if we need a full set of create, read, update, and delete operations 
# for expense objects that are accessible via API, 
# while maintaining the ability to filter based on the fields specified.
class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'name', 'amount', 'created_at', 'category']
    def get_queryset(self):
        queryset = Expense.objects.filter(budget__user=self.request.user)
        budget_id = self.request.query_params.get('id', None)
        if budget_id is not None:
            queryset = queryset.filter(budget__id=budget_id)
        return queryset
    
class ExpenseDetailView(generics.RetrieveAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        userName = self.request.user
        return Expense.objects.filter(budget__user=userName)
    
class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    # override get_queryset() to return only budgets for the authenticated user
    def get_queryset(self):
        # This allows us to filter based on query parameters passed in the URL 
        queryset = Expense.objects.filter(budget__user=self.request.user)  # Ensure expenses are for the authenticated user
        budget_id = self.request.query_params.get('id', None)
    
        if budget_id is not None:
            queryset = queryset.filter(budget__id=budget_id)  # Further filter by budget_id if provided
        return queryset

    # override perform_create() to add the budget to the user
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save() 
        else: 
            print(serializer.errors)

class ExpenseDeleteView(generics.DestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        userName = self.request.user
        return Expense.objects.filter(budget__user=self.request.user) 

class IncomeListCreateView(generics.ListCreateAPIView):
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]

    # override get_queryset() to return only income for the authenticated user
    def get_queryset(self):
        userName = self.request.user #.request allows you to access to request object that allows you to specify the user
        return Income.objects.filter(user=userName) 

    # override perform_create() to add the income to the user
    def perform_create(self, serializer):
        print (self.request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user) # have to manually pass in the user, cause it is a read-only field
        else: 
            print(serializer.errors)

class IncomeDeleteView(generics.DestroyAPIView):
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        userName = self.request.user
        return Income.objects.filter(user=userName) 

class CategoryListView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.all()
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)




@api_view(['GET'])
def analytics(request):
    user = request.user
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Get month parameter from request
    month_param = request.query_params.get('month', str(current_month))
    try:
        month = datetime.strptime(month_param, '%B').month  # Convert month name to month number
    except ValueError:
        month = int(month_param)  # Try to convert directly to an integer if parsing fails




    # 1. Most spent on category for the selected month
    most_spent_category = Expense.objects.filter(budget__user=user, created_at__year=current_year, created_at__month=month) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('-total_spent') \
        .first()
    
    # 2. Least spent on category for the selected month
    least_spent_category = Expense.objects.filter(budget__user=user, created_at__year=current_year, created_at__month=month, category__isnull=False) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('total_spent') \
        .first()

    # 3. Average monthly spent
    start_date = datetime.now() - timedelta(days=30)
    average_monthly_spent = Expense.objects.filter(budget__user=user, created_at__gte=start_date) \
        .aggregate(average_monthly_spent=Avg('amount'))['average_monthly_spent']

    # 4. Net income (total income - total expenses) for the selected month
    total_income_selected_month = Income.objects.filter(user=user, created_at__year=current_year, created_at__month=month) \
        .aggregate(total_income=Sum('amount'))['total_income'] or 0

    total_expenses_selected_month = Expense.objects.filter(budget__user=user, created_at__year=current_year, created_at__month=month) \
        .aggregate(total_expenses=Sum('amount'))['total_expenses'] or 0

    net_income_selected_month = total_income_selected_month - total_expenses_selected_month

    # Additional Statistics
    # 5. Spending per Month
    spending_per_month = Expense.objects.filter(budget__user=user) \
        .annotate(month=ExtractMonth('created_at')) \
        .values('month') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('month')

    # 4a. Net income (total income - total expenses) per month
    total_income_per_month = Income.objects.filter(user=user) \
        .annotate(month=ExtractMonth('created_at')) \
        .values('month') \
        .annotate(total_income=Sum('amount')) \
        .order_by('month')

    # Create a dictionary for easy lookup of expenses by month
    expenses_dict = {expense['month']: expense['total_spent'] for expense in spending_per_month}

    net_income_per_month = []
    for income in total_income_per_month:
        month_income = income['month']
        total_income = income['total_income']
        total_expenses = expenses_dict.get(month_income, 0)
        net_income_per_month.append({
            'month': month_income,
            'net_income': total_income - total_expenses
        })

    # 6. Spending by Category for the selected month
    spending_by_category = Expense.objects.filter(budget__user=user, created_at__year=current_year, created_at__month=month) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('-total_spent')
    
    # 7. Total spending for the selected month
    total_spent_selected_month = Expense.objects.filter(
        budget__user=user, 
        created_at__year=current_year, 
        created_at__month=month
    ).aggregate(total_spent=Sum('amount'))['total_spent']

    # 8. Spending by Category per Month
    spending_by_category_per_month = Expense.objects.filter(budget__user=user) \
        .annotate(month=ExtractMonth('created_at')) \
        .values('category__name', 'month') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('category__name', 'month')
    
    # 9. Number of Budgets Exceeded for the Selected Month
    budgets_exceeded = Budget.objects.filter(user=user, created_at__year=current_year, created_at__month=month) \
        .annotate(total_spent=Sum('expense__amount')) \
        .filter(total_spent__gt=F('amount')) \
        .count()

    # 10. Weekly Expenses for the Selected Month
    weekly_expenses = Expense.objects.filter(budget__user=user, created_at__year=current_year, created_at__month=month) \
        .annotate(week=ExtractWeek('created_at')) \
        .values('week') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('week')

    data = {
        'most_spent_category': most_spent_category,
        'least_spent_category': least_spent_category,
        'average_monthly_spent': average_monthly_spent,
        'net_income_current_month': net_income_selected_month,
        'net_income_per_month': list(net_income_per_month),
        'spending_per_month': list(spending_per_month),
        'spending_by_category': list(spending_by_category),
        'total_spent_current_month': total_spent_selected_month,
        'spending_by_category_per_month': list(spending_by_category_per_month),
        'budgets_exceeded': budgets_exceeded,
        'weekly_expenses': list(weekly_expenses)
    }

    return Response(data)

class StudentDiscountListView(generics.ListAPIView):
    queryset = StudentDiscount.objects.all()
    serializer_class = StudentDiscountSerializer


class GoalDetailView(generics.RetrieveAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        goal = Goal.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()
        if not goal:
            raise NotFound("Goal not found")
        return goal

class GoalListCreateView(generics.ListCreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GoalDeleteView(generics.DestroyAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response_data = {'success': 'Goal deleted', 'message': 'Goal deleted successfully'}
        print("Delete Response Data:", response_data)
        return Response(response_data, status=status.HTTP_200_OK)

class AddSavingsToGoalView(generics.GenericAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()
        if not goal:
            raise NotFound("Goal not found")
        
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount)
            goal.add_savings(amount)
            return Response(self.get_serializer(goal).data, status=status.HTTP_200_OK)
        except InvalidOperation:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

class RedeemGoalView(generics.GenericAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()
        if not goal:
            response_data = {'error': 'Goal not found'}
            print("Redeem Response Data:", response_data)
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        if goal.is_goal_achieved():
            goal.redeem()
            response_data = {'success': 'Goal redeemed', 'message': 'Goal redeemed successfully'}
            print("Redeem Response Data:", response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {'error': 'Goal not achieved yet'}
            print("Redeem Response Data:", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        



class ExportDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Fetch the user's expenses and income data
        budgets = Budget.objects.filter(user=user)
        expenses = Expense.objects.filter(budget__in=budgets)
        income = Income.objects.filter(user=user)

        # Create a new Excel workbook
        wb = Workbook()
        ws_expenses = wb.active
        ws_expenses.title = "Expenses"

        # Write the expenses data to the workbook
        ws_expenses.append(["Date", "Category", "Amount", "Description"])
        for expense in expenses:
            ws_expenses.append([expense.created_at.strftime('%Y-%m-%d'), expense.category.name, expense.amount, expense.name])

        # Create a new sheet for income data
        ws_income = wb.create_sheet(title="Income")
        ws_income.append(["Date", "Source", "Amount"])
        for inc in income:
            ws_income.append([inc.created_at.strftime('%Y-%m-%d'), inc.name, inc.amount])

        # Prepare the response
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = 'attachment; filename=financial_data.xlsx'
        wb.save(response)

        return response
