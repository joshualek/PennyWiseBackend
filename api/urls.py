from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from .views import ExpenseViewSet
from .views import analytics
from .views import ExportDataView

router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet, basename='expense')


urlpatterns = [
    path("budgets/", views.BudgetListCreateView.as_view(), name="budget-list"),
    path("budgets/<int:pk>/", views.BudgetDetailView.as_view(), name="budget-detail"),
    path("budgets/delete/<int:pk>/", views.BudgetDeleteView.as_view(), name="delete-budget"),
    path("expenses/", views.ExpenseListCreateView.as_view(), name="expense-list"),
    path("expenses/<int:pk>/", views.ExpenseDetailView.as_view(), name="expense-detail"),
    path("expenses/delete/<int:pk>/", views.ExpenseDeleteView.as_view(), name="delete-expense"),
    path("income/", views.IncomeListCreateView.as_view(), name="income-list"),
    path("income/delete/<int:pk>/", views.IncomeDeleteView.as_view(), name="delete-income"),
    path("category/", views.CategoryListView.as_view(), name="category-list"),
    path('analytics/', analytics, name="analytics"),
    path("student-discount/", views.StudentDiscountListView.as_view(), name="student-discount-list"),
    path('goals/', views.GoalListCreateView.as_view(), name='goal-list-create'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/delete/<int:pk>/', views.GoalDeleteView.as_view(), name='goal-delete'),
    path('goals/<int:pk>/add-savings/', views.AddSavingsToGoalView.as_view(), name='add-savings-to-goal'),
    path('goals/<int:pk>/redeem/', views.RedeemGoalView.as_view(), name='redeem-goal'),
    path('export/', ExportDataView.as_view(), name='export-data'),
    path('', include(router.urls)),

]
