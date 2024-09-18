from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Root1234'
app.config['MYSQL_DB'] = 'pythonlogin'

mysql = MySQL(app)

class CheckingAccount:
    def __init__(self, name, balance):
        self.name = name
        self.balance = balance 
        self.option = "checking"
    def deposit(self, amount):
        self.balance += amount
        return f"Your bank balance is is {self.balance}"
    def withdraw(self, amount):
        if self.balance - amount < 0:
            return Exception("Not allowed. Your balance can not be negative.")
        self.balance -= amount
        return f"Your deposit in the bank is {self.balance}"
    def __str__(self):
        return f"CheckingAccount(name={self.name}, balance={self.balance})"
class SavingsAccount():
    def __init__(self, name, balance, interest_rate):
        self.name = name
        self.balance = balance
        self.interest_rate = interest_rate
        self.option = "savings"
    def deposit(self, amount):
        self.balance += amount
        return f"Your savings balance is {self.balance}"
    def __str__(self):
        return f"SavingsAccount(name ={self.name}, interest rate ={self.interest_rate} balance ={self.balance})"
    def apply_daily_interest(self):
        #first convert the annual interest rate to daily
        daily_rate = self.interest_rate / 365
        daily_interest = self.balance * round(daily_rate,2)
        if daily_interest <0:
            return Exception("Savings can not be negative")
        self.balance +=daily_interest
        return f"Your savings account holds {self.balance}"

class CreditAccount():
    def __init__(self, name, interest_rate, credit_limit):
        self.name = name
        self.balance = 0  # Initial balance is always 0
        self.interest_rate = interest_rate
        self.credit_limit = credit_limit
        self.option = "credit"

    def deposit(self, amount):
        # Deposit adds to the balance (it can go positive after deposit)
        self.balance += amount
        return f"Your credit account balance is {self.balance}"

    def withdraw(self, amount):
        # Allow withdrawal only if it does not exceed the credit limit
        if self.balance - amount < -self.credit_limit:
            return Exception("Not allowed. Exceeds credit limit.")
        self.balance -= amount
        return f"Your credit account balance is {self.balance}"

    def apply_daily_interest(self):
        # Apply interest only if the balance is negative
        if self.balance < 0:
            daily_rate = self.interest_rate / 365
            daily_interest = self.balance * daily_rate
            self.balance += daily_interest
        return f"Your credit account balance is {self.balance}"


class Bank():
    def __init__(self):
        self.account = [] 
    def open_savings(self, name, balance, interest_rate):
        new_account = SavingsAccount(name, balance, interest_rate)
        self.account.append(new_account)
        return f"The saving account you opened is named {name} with a balance of {balance}"
    def open_checking(self, name, balance):
        new_account = CheckingAccount(name, balance)
        self.account.append(new_account)
        return f"The checking account you opened is named {name} with a balance of {balance}"
    def open_credit(self, name, balance, interest_rate, credit_limit):
        new_account = CreditAccount(name, balance, interest_rate, credit_limit)
        self.account.append(new_account)
        return f"The credit account you opened is named {name} with a balance of {balance}"
    def display_accounts(self):
        for account in self.account:
            print(account)
    def apply_daily_interest(self):
        for account in self.account:
            if isinstance(account, SavingsAccount) or isinstance(account, CreditAccount):
                account.apply_daily_interest()

    def total_cash(self):
        return sum(account.balance for account in self.account if isinstance(account, SavingsAccount) or isinstance(account, CheckingAccount))

    def total_credit(self):
        return sum(account.balance for account in self.account if isinstance(account, CreditAccount))

    def account_exists(self, name, option):
        for account in self.account:
            if account.name == name and account.option == option:
                return True
            return False

bank = Bank()
@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM pythonlogin where username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = ''
            return render_template('main.html')
        else:    
            msg = 'The account does not exist'
    return render_template('index.html', msg=msg)

@app.route('/main') 
def main():
    return render_template('main.html')

@app.route('/view_account')
def view_account():
    accounts = bank.account
    return render_template('view_account.html', accounts=accounts)

@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    if request.method == 'POST':
        name = request.form['name']
        option = request.form['option']
        option2 = request.form['option2']
        error_message = None

        try:
            amount2 = float(request.form['amount2'])
        except ValueError:
            amount2 = None
        if not bank.account_exists(name, option):
            error_message = "Account does not exist"
            return render_template("transaction.html", error=error_message)
            
        account = next((acc for acc in bank.account if acc.name == name and acc.option == option), None)

        if option2 == 'deposit':
            account.deposit(amount2)
        elif option2 == 'withdraw':
            account.withdraw(amount2)
            
        return redirect(url_for('view_account'))
    bank.display_accounts()
    return render_template("transaction.html")

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    error_message = None
    if request.method == 'POST':
        name = request.form['name']
        try:
            balance = float(request.form['balance'])
        except ValueError:
            balance = None  # Set balance to None if conversion fails
        option = request.form['option']

        if name == '' or balance is None:
            error_message = "Please enter a name and a balance"
            return render_template("create_account.html", error=error_message)

        if bank.account_exists(name, option):
            error_message = "Account already exists"
            return render_template("create_account.html", error=error_message)
        else:
            if option == 'savings':
                bank.open_savings(name, balance, interest_rate=2)
            elif option == 'checking':
                bank.open_checking(name, balance)
            elif option == 'credit':
                # Force balance to 0 for credit account
                balance = 0  
                bank.open_credit(name, balance=0, interest_rate=5, credit_limit=500)

        bank.display_accounts()

        return redirect(url_for('view_account'))
    return render_template("create_account.html", error=error_message)
if __name__ == "__main__":
    app.run(debug=True)