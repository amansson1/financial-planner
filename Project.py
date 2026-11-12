from bakery import assert_equal
from dataclasses import dataclass
from drafter import *

@dataclass
class State:
    age: int
    salary: float
    contribution_percentage: float
    live: str
    accounts: list[Account]
    expenses: list[Expense]

@dataclass
class Account:
    name: str
    amount: float

@dataclass
class Expense:
    name: str
    amount: float


@route
def index(state: State) -> Page:
    return Page(state, [
        "Age:",
        TextBox("new_age", state.age, int),
        "\n",
        "Salary:",
        TextBox("new_salary", state.salary, float),
        "\n",
        "Retirement Contribution Percentage:",
        TextBox("new_contribution_percentage", state.contribution_percentage, float),
        Button("Update", "update")
    ])


def traditional_401k(salary: float, age: int, percentage: float) -> float:
    if age < 50:
        maximum = 24500
    elif age >= 60 and age <= 63:
        maximum = 24500 + 11250
    else:
        maximum = 24500 + 8000
    if salary * percentage <= maximum:
        contribution = salary * percentage
    else:
        contribution = maximum
    return contribution

assert_equal(traditional_401k(100000.0, 20, 0.15), 15000.0)

def fed_tax(salary: float) -> float:
    salary = salary - 16100
    a = 12400 * 0.1
    b = 38000 * 0.12
    c = 55300 * 0.22
    d = 96075 * 0.24
    e = 54450 * 0.32
    f = 384375 * 0.35
    if salary <= 0:
        tax = 0.0
    elif salary <= 12400:
        tax = salary*0.1
    elif salary <= 50400:
        tax = a + (salary-12400)*0.12
    elif salary <= 105700:
        tax = a + b + (salary-50400)*0.22
    elif salary <= 201775:
        tax = a + b + c + (salary-105700)*0.24
    elif salary <= 256225:
        tax = a + b + c + d + (salary-201775)*0.32
    elif salary <= 640600:
        tax = a + b + c + d + e + (salary-256225)*0.35
    else:
        tax = a + b + c + d + e + f + (salary-640600)*0.37
    return tax

assert_equal(fed_tax(100000.0), 13170.0)

def social_security_tax(salary: float) -> float:
    if salary <= 184500:
        tax = salary * 0.062
    else:
        tax = 184500 * 0.062
    return tax

assert_equal(social_security_tax(100000.0), 6200.0)

def medicare_tax(salary: float) -> float:
    if salary <= 200000:
        tax = salary * 0.0145
    else:
        tax = salary * 0.0145 + (salary-200000)*0.009
    return tax

assert_equal(medicare_tax(100000.0), 1450.0)

def de_tax(salary: float) -> float:
    if salary <= 9400:
        tax = 0.0
    else:
        salary = salary - 3250
        a = 3000 * 0.022
        b = 5000 * 0.039
        c = 10000 * 0.048
        d = 5000 * 0.052
        e = 35000 * 0.0555
        if salary <= 2000:
            tax = 0.0
        elif salary <= 5000:
            tax = (salary - 2000)*0.022
        elif salary <= 10000:
            tax = a + (salary - 5000)*0.039
        elif salary <= 20000:
            tax = a + b + (salary - 10000)*0.048
        elif salary <= 25000:
            tax = a + b + c + (salary - 20000)*0.052
        elif salary <= 60000:
            tax = a + b + c + d + (salary - 25000)*0.0555
        else:
            tax = a + b + c + d + e + (salary - 60000)*0.066
    return tax

assert_equal(de_tax(100000.0), 5369.0)

def after_tax_income(salary: float) -> float:
    fed = fed_tax(salary)
    ssa = social_security_tax(salary)
    medicare = medicare_tax(salary)
    total_tax = fed + ssa + medicare
    return salary - total_tax

assert_equal(after_tax_income(100000.0), 79180.0)

