"""
Paycheck & Retirement Planner (CS1 Final Project, built with Drafter).

The user enters their age, salary, desired 401(k) contribution and home state,
then adds monthly expenses and savings accounts. The site calculates taxes,
paychecks, and savings.

KEY IDEA: a traditional 401(k) contribution lowers federal (and Delaware)
taxable income, but Social Security and Medicare tax are still charged on the
full salary. That is why the tax functions below take both `salary` and
`contribution`.

All dollar amounts are 2026 single-filer figures. Expenses are MONTHLY.
Percentages are stored as fractions (0.15) but typed by the user as 15.
"""
from bakery import assert_equal
from dataclasses import dataclass
from drafter import *

# Global CONSTANTS (allowed): they never change while the program runs.
MONTHS_PER_YEAR = 12
BIWEEKLY_PERIODS = 26
SEMIMONTHLY_PERIODS = 24
MIN_AGE = 16
MAX_AGE = 100
ROTH_PHASE_OUT_START = 153000
ROTH_PHASE_OUT_END = 168000


@dataclass
class Account:
    """A savings or retirement account (name is the account type)."""
    name: str
    amount: float


@dataclass
class Expense:
    """A monthly expense; essential=False means it can be cut."""
    name: str
    amount: float
    essential: bool


@dataclass
class State:
    """Everything that must persist between pages."""
    age: int
    salary: float
    contribution_percentage: float
    live: str
    accounts: list[Account]
    expenses: list[Expense]
    message: str


# ---------------------------------------------------------------------------
# Formatting and validation helpers
# ---------------------------------------------------------------------------

def money(amount: float) -> str:
    """Format a number as dollars, e.g. 1234.5 becomes '$1,234.50'."""
    amount = round(amount, 2)
    sign = ""
    if amount < 0:
        sign = "-"
        amount = -amount
    whole, cents = ("%.2f" % amount).split(".")
    grouped = ""
    while len(whole) > 3:
        grouped = "," + whole[-3:] + grouped
        whole = whole[:-3]
    return sign + "$" + whole + grouped + "." + cents

assert_equal(money(1234.5), "$1,234.50")
assert_equal(money(0.0), "$0.00")
assert_equal(money(-5.0), "-$5.00")
assert_equal(money(1234567.891), "$1,234,567.89")


def is_valid_number(text: str) -> bool:
    """Return True if text is a non-negative number such as '12' or '12.50'."""
    return text.replace(".", "", 1).isdigit()

assert_equal(is_valid_number("12.50"), True)
assert_equal(is_valid_number("12"), True)
assert_equal(is_valid_number("abc"), False)
assert_equal(is_valid_number(""), False)
assert_equal(is_valid_number("-5"), False)
assert_equal(is_valid_number("1.2.3"), False)


def profile_error(age_text: str, salary_text: str, percent_text: str) -> str:
    """Return a message describing what is wrong with the profile form, or '' if it is fine."""
    if not age_text.isdigit() or not is_valid_number(salary_text) or not is_valid_number(percent_text):
        return "Please enter a whole number for age and plain numbers for salary and percentage."
    if int(age_text) < MIN_AGE or int(age_text) > MAX_AGE:
        return "Age must be between " + str(MIN_AGE) + " and " + str(MAX_AGE) + "."
    if float(percent_text) > 100:
        return "Contribution percentage cannot be more than 100."
    return ""

assert_equal(profile_error("30", "50000", "10"), "")
assert_equal(profile_error("abc", "50000", "10"),
             "Please enter a whole number for age and plain numbers for salary and percentage.")
assert_equal(profile_error("5", "50000", "10"), "Age must be between 16 and 100.")
assert_equal(profile_error("30", "50000", "150"), "Contribution percentage cannot be more than 100.")


# ---------------------------------------------------------------------------
# Retirement and tax calculations
# ---------------------------------------------------------------------------

def traditional_401k_limit(age: int) -> float:
    """Return the 2026 employee 401(k) contribution limit for someone of this age."""
    base_limit = 24500
    if age < 50:
        return float(base_limit)
    elif age >= 60 and age <= 63:
        return float(base_limit + 11250)
    else:
        return float(base_limit + 8000)

assert_equal(traditional_401k_limit(30), 24500.0)
assert_equal(traditional_401k_limit(55), 32500.0)
assert_equal(traditional_401k_limit(61), 35750.0)
assert_equal(traditional_401k_limit(64), 32500.0)


def traditional_401k(salary: float, age: int, percentage: float) -> float:
    """Return the yearly 401(k) contribution: salary * percentage, capped at the age limit."""
    wanted = salary * percentage
    limit = traditional_401k_limit(age)
    if wanted <= limit:
        return wanted
    return limit

assert_equal(traditional_401k(100000.0, 20, 0.15), 15000.0)
assert_equal(traditional_401k(200000.0, 30, 0.5), 24500.0)
assert_equal(traditional_401k(0.0, 30, 0.5), 0.0)


def retirement_note(wanted: float, limit: float) -> str:
    """Return a sentence comparing the wanted contribution with the legal limit."""
    if wanted > limit:
        return "Your percentage is above the IRS limit, so your contribution is capped at " + money(limit) + "."
    elif wanted == limit:
        return "You are contributing exactly the IRS limit."
    else:
        return "You could contribute up to " + money(limit - wanted) + " more this year."

assert_equal(retirement_note(30000.0, 24500.0),
             "Your percentage is above the IRS limit, so your contribution is capped at $24,500.00.")
assert_equal(retirement_note(24500.0, 24500.0), "You are contributing exactly the IRS limit.")
assert_equal(retirement_note(15000.0, 24500.0), "You could contribute up to $9,500.00 more this year.")


def retirement_account(salary: float) -> str:
    """Return which extra IRA the person can use, based on 2026 Roth IRA income limits."""
    if salary < ROTH_PHASE_OUT_START:
        return "Roth IRA (full contribution allowed)"
    elif salary < ROTH_PHASE_OUT_END:
        return "Roth IRA (reduced contribution)"
    else:
        return "Traditional IRA (income too high for a direct Roth IRA)"

assert_equal(retirement_account(100000.0), "Roth IRA (full contribution allowed)")
assert_equal(retirement_account(160000.0), "Roth IRA (reduced contribution)")
assert_equal(retirement_account(200000.0), "Traditional IRA (income too high for a direct Roth IRA)")


def fed_tax(salary: float) -> float:
    """Return federal income tax on a salary, after the $16,100 standard deduction (2026, single)."""
    taxable = salary - 16100
    tax_10 = 12400 * 0.1
    tax_12 = 38000 * 0.12
    tax_22 = 55300 * 0.22
    tax_24 = 96075 * 0.24
    tax_32 = 54450 * 0.32
    tax_35 = 384375 * 0.35
    if taxable <= 0:
        tax = 0.0
    elif taxable <= 12400:
        tax = taxable * 0.1
    elif taxable <= 50400:
        tax = tax_10 + (taxable - 12400) * 0.12
    elif taxable <= 105700:
        tax = tax_10 + tax_12 + (taxable - 50400) * 0.22
    elif taxable <= 201775:
        tax = tax_10 + tax_12 + tax_22 + (taxable - 105700) * 0.24
    elif taxable <= 256225:
        tax = tax_10 + tax_12 + tax_22 + tax_24 + (taxable - 201775) * 0.32
    elif taxable <= 640600:
        tax = tax_10 + tax_12 + tax_22 + tax_24 + tax_32 + (taxable - 256225) * 0.35
    else:
        tax = tax_10 + tax_12 + tax_22 + tax_24 + tax_32 + tax_35 + (taxable - 640600) * 0.37
    return tax

assert_equal(fed_tax(100000.0), 13170.0)
assert_equal(fed_tax(10000.0), 0.0)
assert_equal(fed_tax(85000.0), 9870.0)


def social_security_tax(salary: float) -> float:
    """Return Social Security tax (6.2%, up to the $184,500 wage base)."""
    if salary <= 184500:
        tax = salary * 0.062
    else:
        tax = 184500 * 0.062
    return tax

assert_equal(social_security_tax(100000.0), 6200.0)
assert_equal(social_security_tax(300000.0), 11439.0)


def medicare_tax(salary: float) -> float:
    """Return Medicare tax (1.45%, plus 0.9% on salary above $200,000)."""
    if salary <= 200000:
        tax = salary * 0.0145
    else:
        tax = salary * 0.0145 + (salary - 200000) * 0.009
    return tax

assert_equal(medicare_tax(100000.0), 1450.0)
assert_equal(medicare_tax(300000.0), 5250.0)


def de_tax(salary: float) -> float:
    """Return Delaware income tax on a salary, after the $3,250 standard deduction."""
    if salary <= 9400:
        tax = 0.0
    else:
        taxable = salary - 3250
        tax_2_2 = 3000 * 0.022
        tax_3_9 = 5000 * 0.039
        tax_4_8 = 10000 * 0.048
        tax_5_2 = 5000 * 0.052
        tax_5_55 = 35000 * 0.0555
        if taxable <= 2000:
            tax = 0.0
        elif taxable <= 5000:
            tax = (taxable - 2000) * 0.022
        elif taxable <= 10000:
            tax = tax_2_2 + (taxable - 5000) * 0.039
        elif taxable <= 20000:
            tax = tax_2_2 + tax_3_9 + (taxable - 10000) * 0.048
        elif taxable <= 25000:
            tax = tax_2_2 + tax_3_9 + tax_4_8 + (taxable - 20000) * 0.052
        elif taxable <= 60000:
            tax = tax_2_2 + tax_3_9 + tax_4_8 + tax_5_2 + (taxable - 25000) * 0.0555
        else:
            tax = tax_2_2 + tax_3_9 + tax_4_8 + tax_5_2 + tax_5_55 + (taxable - 60000) * 0.066
    return tax

assert_equal(de_tax(100000.0), 5369.0)
assert_equal(de_tax(5000.0), 0.0)
assert_equal(de_tax(85000.0), 4379.0)


def state_income_tax(salary: float, contribution: float, live: str) -> float:
    """Return state income tax; only Delaware is calculated. 401(k) money is not taxed by DE."""
    if live == "DE":
        return de_tax(salary - contribution)
    return 0.0

assert_equal(state_income_tax(100000.0, 15000.0, "DE"), 4379.0)
assert_equal(state_income_tax(100000.0, 15000.0, "Other"), 0.0)


def federal_tax_savings(salary: float, contribution: float) -> float:
    """Return how much federal tax the 401(k) contribution saves."""
    return fed_tax(salary) - fed_tax(salary - contribution)

assert_equal(federal_tax_savings(100000.0, 15000.0), 3300.0)
assert_equal(federal_tax_savings(100000.0, 0.0), 0.0)


def total_tax(salary: float, contribution: float, live: str) -> float:
    """Return all yearly taxes. Only federal and state tax use salary minus the 401(k) contribution;
    Social Security and Medicare are charged on the full salary."""
    federal = fed_tax(salary - contribution)
    social_security = social_security_tax(salary)
    medicare = medicare_tax(salary)
    state = state_income_tax(salary, contribution, live)
    return federal + social_security + medicare + state

assert_equal(total_tax(100000.0, 15000.0, "DE"), 21899.0)
assert_equal(total_tax(100000.0, 15000.0, "Other"), 17520.0)


def net_income(salary: float, contribution: float, live: str) -> float:
    """Return yearly take-home pay after the 401(k) contribution and all taxes."""
    return salary - contribution - total_tax(salary, contribution, live)

assert_equal(net_income(100000.0, 15000.0, "DE"), 63101.0)
assert_equal(net_income(0.0, 0.0, "DE"), 0.0)


def paycheck(net_yearly: float, periods: int) -> float:
    """Return one paycheck when take-home pay is split into this many pay periods."""
    return net_yearly / periods

assert_equal(paycheck(52000.0, 26), 2000.0)
assert_equal(paycheck(60000.0, 24), 2500.0)


# ---------------------------------------------------------------------------
# Expense and account helpers (these loop over the lists of dataclass instances)
# ---------------------------------------------------------------------------

def total_expenses(expense_list: list[Expense]) -> float:
    """Return the sum of the amount of every expense in the list."""
    total = 0.0
    for expense in expense_list:
        total += expense.amount
    return total

assert_equal(total_expenses([]), 0.0)
assert_equal(total_expenses([Expense("Rent", 1500.0, True), Expense("Tv", 15.0, False)]), 1515.0)


def essential_expenses(expense_list: list[Expense]) -> list[Expense]:
    """Return a new list holding only the expenses that are essential (filters out the rest)."""
    kept = []
    for expense in expense_list:
        if expense.essential:
            kept.append(expense)
    return kept

assert_equal(essential_expenses([]), [])
assert_equal(essential_expenses([Expense("Rent", 1500.0, True), Expense("Tv", 15.0, False)]),
             [Expense("Rent", 1500.0, True)])


def expense_lines(expense_list: list[Expense]) -> list[str]:
    """Return one display line per expense, marking the non-essential ones."""
    lines = []
    for expense in expense_list:
        line = expense.name + ": " + money(expense.amount) + " per month"
        if not expense.essential:
            line += " (non-essential)"
        lines.append(line)
    return lines

assert_equal(expense_lines([Expense("Rent", 1500.0, True), Expense("Tv", 15.0, False)]),
             ["Rent: $1,500.00 per month", "Tv: $15.00 per month (non-essential)"])


def total_savings(account_list: list[Account]) -> float:
    """Return the combined balance of all accounts."""
    total = 0.0
    for account in account_list:
        total += account.amount
    return total

assert_equal(total_savings([]), 0.0)
assert_equal(total_savings([Account("Savings", 500.0), Account("Roth IRA", 250.0)]), 750.0)


def account_lines(account_list: list[Account]) -> list[str]:
    """Return one display line per account."""
    lines = []
    for account in account_list:
        lines.append(account.name + ": " + money(account.amount))
    return lines

assert_equal(account_lines([Account("Savings", 500.0)]), ["Savings: $500.00"])


def add_or_update_account(account_list: list[Account], name: str, amount: float) -> None:
    """Add amount to the account with this name (ignoring capitalization), or create it."""
    for account in account_list:
        if account.name.lower() == name.lower():
            account.amount += amount
            return
    account_list.append(Account(name, amount))

def test_add_or_update_account() -> None:
    """Unit test helper: checks that existing accounts are merged and new ones are created."""
    accounts_to_test = [Account("Savings", 500.0)]
    add_or_update_account(accounts_to_test, "savings", 250.0)
    assert_equal(accounts_to_test, [Account("Savings", 750.0)])
    add_or_update_account(accounts_to_test, "Roth IRA", 100.0)
    assert_equal(accounts_to_test, [Account("Savings", 750.0), Account("Roth IRA", 100.0)])

test_add_or_update_account()


def annual_leftover(net_yearly: float, expense_list: list[Expense]) -> float:
    """Return yearly take-home pay minus a year of expenses (negative means over budget)."""
    return net_yearly - total_expenses(expense_list) * MONTHS_PER_YEAR

assert_equal(annual_leftover(60000.0, [Expense("Rent", 2000.0, True)]), 36000.0)
assert_equal(annual_leftover(10000.0, [Expense("Rent", 1000.0, True)]), -2000.0)


def budget_advice(monthly_leftover: float) -> str:
    """Return advice: spend less if over budget, otherwise encourage saving the leftover."""
    if monthly_leftover < 0:
        return "You are over budget by " + money(-monthly_leftover) + " per month. Try cutting non-essential expenses."
    elif monthly_leftover == 0:
        return "Your budget is exactly balanced."
    else:
        return "You have " + money(monthly_leftover) + " left each month. Consider depositing it into an account."

assert_equal(budget_advice(-100.0),
             "You are over budget by $100.00 per month. Try cutting non-essential expenses.")
assert_equal(budget_advice(0.0), "Your budget is exactly balanced.")
assert_equal(budget_advice(250.0),
             "You have $250.00 left each month. Consider depositing it into an account.")


def take_message(state: State) -> str:
    """Return the pending feedback message and clear it so it only shows once."""
    note = state.message
    state.message = ""
    return note


def sample_state() -> State:
    """Return a ready-made State used only by the unit tests below."""
    return State(30, 100000.0, 0.15, "DE", [Account("Savings", 500.0)],
                 [Expense("Rent", 1500.0, True), Expense("Streaming", 15.0, False)], "")

assert_equal(take_message(State(30, 0.0, 0.0, "DE", [], [], "Hi")), "Hi")


# ---------------------------------------------------------------------------
# Pages (routes)
# ---------------------------------------------------------------------------

def nav_links() -> list:
    """Return the navigation Links shown at the top of every page except the home page."""
    return [Link("Home", index), " | ", Link("Retirement", retirement), " | ",
            Link("Taxes", taxes), " | ", Link("Expenses", expenses), " | ",
            Link("Accounts", accounts), " | ", Link("Outcome", outcome),
            LineBreak(), HorizontalRule()]


@route
def index(state: State) -> Page:
    """Home page: collects age, salary, 401(k) percentage and home state."""
    note = take_message(state)
    return Page(state, [
        Header("Paycheck & Retirement Planner"),
        "Enter your details to see your taxes, paycheck, and savings.",
        LineBreak(),
        note,
        LineBreak(),
        "Age:",
        TextBox("new_age", str(state.age)),
        LineBreak(),
        "Yearly salary ($):",
        TextBox("new_salary", str(state.salary)),
        LineBreak(),
        "Retirement (401k) contribution, % of salary:",
        TextBox("new_contribution_percentage", str(round(state.contribution_percentage * 100, 2))),
        LineBreak(),
        "Where do you live?",
        SelectBox("new_live", ["DE", "Other"], state.live),
        LineBreak(),
        Button("Save and Continue", update_profile),
    ])



@route
def update_profile(state: State, new_age: str, new_salary: str,
                   new_contribution_percentage: str, new_live: str) -> Page:
    """Validate the home-page form, save it into the State, and move on to the retirement page."""
    error = profile_error(new_age.strip(), new_salary.strip(), new_contribution_percentage.strip())
    if error != "":
        state.message = error
        return index(state)
    state.age = int(new_age.strip())
    state.salary = float(new_salary.strip())
    state.contribution_percentage = float(new_contribution_percentage.strip()) / 100
    state.live = new_live
    return retirement(state)



@route
def retirement(state: State) -> Page:
    """Show the 401(k) contribution, its limit, the tax it saves, and a suggested IRA."""
    wanted = state.salary * state.contribution_percentage
    limit = traditional_401k_limit(state.age)
    contribution = traditional_401k(state.salary, state.age, state.contribution_percentage)
    return Page(state, nav_links() + [
        Header("Retirement"),
        BulletedList([
            "Yearly 401(k) contribution: " + money(contribution),
            "Per bi-weekly paycheck: " + money(contribution / BIWEEKLY_PERIODS),
            "2026 limit for your age: " + money(limit),
            retirement_note(wanted, limit),
            "Federal tax saved by contributing: " + money(federal_tax_savings(state.salary, contribution)),
            "Suggested extra account: " + retirement_account(state.salary),
        ]),
        "A traditional 401(k) lowers your federal (and Delaware) taxable income. Social Security and "
        "Medicare tax are still charged on your full salary.",
        LineBreak(),
        Link("Next: Taxes", taxes),
    ])



@route
def taxes(state: State) -> Page:
    """Show each yearly tax, calculated with the 401(k) contribution taken into account."""
    contribution = traditional_401k(state.salary, state.age, state.contribution_percentage)
    if state.live == "DE":
        state_label = "Delaware income tax"
    else:
        state_label = "State income tax (not calculated)"
    return Page(state, nav_links() + [
        Header("Taxes"),
        Table([
            ["Tax", "Yearly amount"],
            ["Federal income tax", money(fed_tax(state.salary - contribution))],
            ["Social Security", money(social_security_tax(state.salary))],
            ["Medicare", money(medicare_tax(state.salary))],
            [state_label, money(state_income_tax(state.salary, contribution, state.live))],
            ["Total", money(total_tax(state.salary, contribution, state.live))],
        ]),
        "Federal and state tax are charged on salary minus your 401(k) contribution of " +
        money(contribution) + ". Social Security and Medicare use your full salary.",
        LineBreak(),
        Link("Next: Expenses", expenses),
    ])



@route
def expenses(state: State) -> Page:
    """Show the expense list and a form for adding a new monthly expense."""
    note = take_message(state)
    if len(state.expenses) == 0:
        listing = ["No expenses yet."]
    else:
        listing = expense_lines(state.expenses)
    return Page(state, nav_links() + [
        Header("Monthly Expenses"),
        note,
        LineBreak(),
        "Expense name:",
        TextBox("expense_name", ""),
        LineBreak(),
        "Monthly amount ($):",
        TextBox("expense_amount", ""),
        LineBreak(),
        CheckBox("essential", True),
        "Essential?",
        LineBreak(),
        Button("Add Expense", add_expense),
        HorizontalRule(),
        BulletedList(listing),
        "Total per month: " + money(total_expenses(state.expenses)),
        LineBreak(),
        Link("See essential expenses only", filter_expenses),
    ])



@route
def add_expense(state: State, expense_name: str, expense_amount: str, essential: bool) -> Page:
    """Validate the expense form and append a new Expense to the State."""
    if expense_name.strip() == "" or not is_valid_number(expense_amount.strip()):
        state.message = "Please enter a name and a plain number for the amount."
    else:
        state.expenses.append(Expense(expense_name.strip(), float(expense_amount.strip()), essential))
        state.message = "Added " + expense_name.strip() + "."
    return expenses(state)



@route
def filter_expenses(state: State) -> Page:
    """Show only essential expenses and how much the non-essential ones cost."""
    essentials = essential_expenses(state.expenses)
    extra = total_expenses(state.expenses) - total_expenses(essentials)
    return Page(state, nav_links() + [
        Header("Essential Expenses"),
        BulletedList(expense_lines(essentials)),
        "Essential total per month: " + money(total_expenses(essentials)),
        LineBreak(),
        "Non-essential spending you could cut: " + money(extra) + " per month.",
        LineBreak(),
        Button("Remove Non-Essential Expenses", remove_nonessential),
        LineBreak(),
        Link("Back to Expenses", expenses),
    ])



@route
def remove_nonessential(state: State) -> Page:
    """Delete every non-essential expense from the State."""
    before = len(state.expenses)
    state.expenses = essential_expenses(state.expenses)
    state.message = "Removed " + str(before - len(state.expenses)) + " non-essential expense(s)."
    return expenses(state)



@route
def accounts(state: State) -> Page:
    """Show the savings accounts and a form for adding money to an account."""
    note = take_message(state)
    if len(state.accounts) == 0:
        listing = ["No accounts yet."]
    else:
        listing = account_lines(state.accounts)
    return Page(state, nav_links() + [
        Header("Savings Accounts"),
        note,
        LineBreak(),
        "Account name (for example Savings or Roth IRA):",
        TextBox("account_name", ""),
        LineBreak(),
        "Amount to add ($):",
        TextBox("account_amount", ""),
        LineBreak(),
        Button("Add to Account", add_account),
        HorizontalRule(),
        BulletedList(listing),
        "Total saved: " + money(total_savings(state.accounts)),
        LineBreak(),
        Link("Next: See Your Outcome", outcome),
    ])



@route
def add_account(state: State, account_name: str, account_amount: str) -> Page:
    """Validate the account form and add the money to a new or existing account."""
    if account_name.strip() == "" or not is_valid_number(account_amount.strip()):
        state.message = "Please enter an account name and a plain number for the amount."
    else:
        add_or_update_account(state.accounts, account_name.strip(), float(account_amount.strip()))
        state.message = "Added money to " + account_name.strip() + "."
    return accounts(state)



@route
def outcome(state: State) -> Page:
    """Summarize salary, 401(k), taxes, paychecks, expenses, savings, and budget advice."""
    contribution = traditional_401k(state.salary, state.age, state.contribution_percentage)
    net_yearly = net_income(state.salary, contribution, state.live)
    leftover = annual_leftover(net_yearly, state.expenses)
    return Page(state, nav_links() + [
        Header("Your Outcome"),
        Table([
            ["Item", "Amount"],
            ["Salary", money(state.salary)],
            ["401(k) contribution (yearly)", money(contribution)],
            ["Total taxes (yearly)", money(total_tax(state.salary, contribution, state.live))],
            ["Take-home pay (yearly)", money(net_yearly)],
            ["Bi-weekly paycheck (26 per year)", money(paycheck(net_yearly, BIWEEKLY_PERIODS))],
            ["Semi-monthly paycheck (24 per year)", money(paycheck(net_yearly, SEMIMONTHLY_PERIODS))],
            ["Expenses (yearly)", money(total_expenses(state.expenses) * MONTHS_PER_YEAR)],
            ["Left over after expenses (yearly)", money(leftover)],
            ["Current savings", money(total_savings(state.accounts))],
            ["Savings after one year", money(total_savings(state.accounts) + leftover)],
        ]),
        LineBreak(),
        budget_advice(leftover / MONTHS_PER_YEAR),
        LineBreak(),
        Link("Change my details", index),
    ])



# Unit tests for every route. They live here, after all routes are defined, because the
# pages link to routes that are defined later in the file.
assert_equal(index(sample_state()).state, sample_state())
assert_equal(update_profile(sample_state(), "40", "120000", "10", "Other").state,
             State(40, 120000.0, 0.1, "Other", [Account("Savings", 500.0)],
                   [Expense("Rent", 1500.0, True), Expense("Streaming", 15.0, False)], ""))
assert_equal(update_profile(sample_state(), "abc", "120000", "10", "DE").state.salary, 100000.0)
assert_equal(retirement(sample_state()).state, sample_state())
assert_equal(taxes(sample_state()).state, sample_state())
assert_equal(expenses(sample_state()).state, sample_state())
assert_equal(add_expense(sample_state(), "Gym", "40", False).state.expenses[2], Expense("Gym", 40.0, False))
assert_equal(len(add_expense(sample_state(), "", "40", False).state.expenses), 2)
assert_equal(len(add_expense(sample_state(), "Gym", "abc", False).state.expenses), 2)
assert_equal(filter_expenses(sample_state()).state, sample_state())
assert_equal(remove_nonessential(sample_state()).state.expenses, [Expense("Rent", 1500.0, True)])
assert_equal(accounts(sample_state()).state, sample_state())
assert_equal(add_account(sample_state(), "savings", "250").state.accounts, [Account("Savings", 750.0)])
assert_equal(add_account(sample_state(), "", "250").state.accounts, [Account("Savings", 500.0)])
assert_equal(outcome(sample_state()).state, sample_state())


# TODO before submitting: save this file as main.py and fill in your repository links.
set_site_information(
    author="Anna Maansson",
    description="Plan your paycheck, taxes, 401(k) contribution, expenses, and savings.",
    sources=["https://drafter-edu.github.io/drafter/"],
    planning=["AI_Conversation.pdf", "CS1_Design.pdf", "CS1_Pick_a_Problem.pdf", "Project.py"],
    links=[https://github.com/amansson1/financial-planner],
)

start_server(State(30, 0.0, 0.0, "DE", [], [], ""))
