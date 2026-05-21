from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from decimal import Decimal

from .forms import RegisterForm, TransactionForm
from .models import Transaction


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'expenses/register.html', {'form': form})


@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)

    total_income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expense = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    balance = total_income - total_expense
    total_savings = balance

    recent_transactions = transactions[:5]

    # Pie chart: expenses by category
    category_data = (
        transactions
        .filter(transaction_type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
    )

    category_labels = [item['category__name'] for item in category_data]
    category_totals = [float(item['total']) for item in category_data]

    highest_category = None
    if category_data:
        highest_category = max(category_data, key=lambda x: x['total'])

    # Bar chart: monthly income vs expense
    monthly_data = (
        transactions
        .annotate(month=TruncMonth('date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    month_dict = {}

    for item in monthly_data:
        month = item['month'].strftime('%b %Y')

        if month not in month_dict:
            month_dict[month] = {'income': 0, 'expense': 0}

        month_dict[month][item['transaction_type']] = float(item['total'])

    monthly_labels = list(month_dict.keys())
    monthly_income = [values['income'] for values in month_dict.values()]
    monthly_expense = [values['expense'] for values in month_dict.values()]

    # Simple budget alert
    # Smart budget alert: expenses should not exceed 75% of income
    budget_limit = total_income * Decimal('0.75')
    budget_alert = None

    if total_income > 0 and total_expense > budget_limit:
        budget_alert = f"You have exceeded 75% of your income. Your recommended spending limit is ₦{budget_limit:,.2f}."

    context = {
        'transactions': transactions,
        'recent_transactions': recent_transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'total_savings': total_savings,

        'category_labels': category_labels,
        'category_totals': category_totals,

        'monthly_labels': monthly_labels,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,

        'highest_category': highest_category,
        'budget_alert': budget_alert,
    }

    return render(request, 'expenses/dashboard.html', context)


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')
    else:
        form = TransactionForm()

    return render(request, 'expenses/add_transaction.html', {'form': form, 'title': 'Add Transaction'})


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)

        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'expenses/add_transaction.html', {'form': form, 'title': 'Edit Transaction'})


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        transaction.delete()
        return redirect('dashboard')

    return render(request, 'expenses/delete_transaction.html', {'transaction': transaction})