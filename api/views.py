from django.contrib.auth.models import User
from django.db.models import Sum, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.timezone import now
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from .serializers import UserSerializer, BudgetSerializer, ExpenseSerializer, IncomeSerializer, CategorySerializer
from .models import Budget, Expense, Income, Category

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

    # 1. Most spent on category
    most_spent_category = Expense.objects.filter(budget__user=user) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('-total_spent') \
        .first()
    
    # 2. Least spent on category
    least_spent_category = Expense.objects.filter(budget__user=user) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('total_spent') \
        .first()


    # 3. Average monthly spent
    start_date = now() - timedelta(days=30)
    average_monthly_spent = Expense.objects.filter(budget__user=user, created_at__gte=start_date) \
        .aggregate(average_monthly_spent=Avg('amount'))['average_monthly_spent']

    # 4. Net income (total income - total expenses)
    total_income = Income.objects.filter(user=user).aggregate(total_income=Sum('amount'))['total_income']
    total_expenses = Expense.objects.filter(budget__user=user).aggregate(total_expenses=Sum('amount'))['total_expenses']
    net_income = total_income - total_expenses

    # Additional Statistics
    # 5. Spending per Month
    spending_per_month = Expense.objects.filter(budget__user=user) \
        .annotate(month=ExtractMonth('created_at')) \
        .values('month') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('month')

    # 6. Spending by Category
    spending_by_category = Expense.objects.filter(budget__user=user) \
        .values('category__name') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('-total_spent')
    
    # 7. Total spending for the current month
    current_year = datetime.now().year
    current_month = datetime.now().month
    total_spent_current_month = Expense.objects.filter(
        budget__user=user, 
        created_at__year=current_year, 
        created_at__month=current_month
    ).aggregate(total_spent=Sum('amount'))['total_spent']

    # 8. Spending by Category per Month
    spending_by_category_per_month = Expense.objects.filter(budget__user=user) \
        .annotate(month=ExtractMonth('created_at')) \
        .values('category__name', 'month') \
        .annotate(total_spent=Sum('amount')) \
        .order_by('category__name', 'month')

    data = {
        'most_spent_category': most_spent_category,
        'average_monthly_spent': average_monthly_spent,
        'net_income': net_income,
        'spending_per_month': list(spending_per_month),
        'spending_by_category': list(spending_by_category),
        'total_spent_current_month': total_spent_current_month,
        'spending_by_category_per_month': list(spending_by_category_per_month)
    }

    return Response(data)
