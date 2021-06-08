import logging
import random
import sys
import json
import time
# import traceback
import psycopg2 as pg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s- %(message)s")


logging.disable(logging.CRITICAL)


class Bank:
    def __init__(self):
        # standard settings when starting program
        self.menu_ = True
        self.menu_create_account = False
        self.menu_login = False
        self.current_user = None
        # menu options
        self.menu_options = ("1", "2", "0")
        self.menu_options_logged = ("1", "2", "3", "4", "5", "0")

        filename = "data_base.json"
        with open(filename) as f:
            my_secrets = json.load(f)
        self.table_name = my_secrets["table_name"]
        self.database_name = my_secrets["database"]
        self.column_names = {"card_name": "card_number", "pin_name": "pin", "balance_name": "balance"}
        self.create_base()
        self.con = pg2.connect(database=my_secrets["database"], user=my_secrets["user"],
                               password=my_secrets["password"])
        self.cur = self.con.cursor()
        self.create_table()

        self.users_to_be_added = 0

    def create_base(self):
        filename = "data_base.json"
        with open(filename) as f:
            my_secrets = json.load(f)
        con = pg2.connect(user=my_secrets["user"], password=my_secrets["password"])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()

        sql_query_create_base = sql.SQL("CREATE DATABASE {database_name}").format(
            database_name=sql.Identifier(self.database_name))

        # noinspection PyUnresolvedReferences
        try:
            cur.execute(sql_query_create_base)
            con.commit()
        except pg2.errors.DuplicateDatabase:
            cur.execute("ROLLBACK")
            con.commit()

    def create_table(self):
        sql_query_create_table = sql.SQL(
            "CREATE TABLE {table_name} (id SERIAL PRIMARY KEY, {card_name} VARCHAR(20) NOT NULL UNIQUE, "
            "{pin_name} VARCHAR(100) NOT NULL, {balance_name} INTEGER DEFAULT 0) ").format(
            table_name=sql.Identifier(self.table_name),
            card_name=sql.Identifier(self.column_names["card_name"]),
            pin_name=sql.Identifier(self.column_names["pin_name"]),
            balance_name=sql.Identifier(self.column_names["balance_name"]))
        # noinspection PyUnresolvedReferences
        try:
            self.cur.execute(sql_query_create_table)
            self.con.commit()
            self.cur.execute("CREATE EXTENSION pgcrypto;")
            self.con.commit()
        except pg2.errors.DuplicateTable:
            self.cur.execute("ROLLBACK")
            self.con.commit()

    # Main function - while loop
    def run_bank(self):
        logging.debug(f"Running, user = {self.current_user}")
        logging.debug(self.users_to_be_added)

        while True:
            if self.menu_ is True:
                self.menu_handle()
            elif self.menu_create_account is True:
                self.menu_create_account_handle()
            elif self.menu_login is True:
                self.menu_login_handle()
            elif self.current_user:
                self.menu_logged_handle()
            logging.debug(f"Running, user = {self.current_user}")
            # logging.debug(self.card_dict)

    # Handles main menu inputs
    def menu_handle(self):
        # handles main menu
        print("1. Create an account", "2. Log into account", "0. Exit", end="\n")

        """if self.users_to_be_added > 0:
            choice = "1"
            self.users_to_be_added -= 1
        else:
            choice = input()"""
        choice = input()
        # asks user as long as he chooses correct entry
        while choice not in self.menu_options:
            print("Entry not recognized")
            print("1. Create an account", "2. Log into account", "0. Exit", end="\n")
            choice = input()
        if choice == "1":
            self.menu_ = False
            self.menu_create_account = True
        elif choice == "2":
            self.menu_ = False
            self.menu_login = True
        elif choice == "0":
            # Those options maybe unnecessary
            self.menu_ = True
            self.menu_create_account = False
            self.menu_login = False
            self.current_user = None
            print("Bye!")
            sys.exit()

    # New Function - handles create account for user
    def menu_create_account_handle(self):
        tic = time.perf_counter()
        # create card number
        self.create_card()

        # exit creating account menu
        self.menu_ = True
        self.menu_create_account = False
        toc = time.perf_counter()
        logging.debug(f"Timed elapsed: {toc - tic:0.10f} seconds")

    # New Function - creates card
    def create_card(self):
        # generate random card and check if is in use currently
        # for testing purposes, delete later
        first_run_check = False
        while True:
            card_number = random.randint(0, 999999999)
            card_number = ("400000" + "0" * (9 - len(str(card_number))) + str(card_number))

            logging.debug(f"Card number: {card_number}, card number length: {len(card_number)}")

            # calculate necessary control sum
            card_number = self.calculate_control_sum(card_number)

            # sql_query = "INSERT INTO testing345(card_number,pin) VALUES (%s, %s)"
            pin = random.randint(0, 9999)
            pin = "0" * (4 - len(str(pin))) + str(pin)
            query_3 = sql.SQL("INSERT INTO {table} ({fields}) VALUES(%s,crypt(%s, gen_salt('bf')))").format(
                fields=sql.SQL(',').join([sql.Identifier(self.column_names["card_name"]),
                                          sql.Identifier(self.column_names["pin_name"]), ]),
                table=sql.Identifier(self.table_name), )

            # for testing purposes, delete later
            if first_run_check:
                card_number = "4000000000000069"
                first_run_check = False
            data = (card_number, pin)
            # noinspection PyUnresolvedReferences
            try:
                # self.cur.execute(sql_query, data)
                self.cur.execute(query_3, data)
                logging.debug("CARD ADDED")
                break

            except pg2.errors.UniqueViolation:
                self.cur.execute("ROLLBACK")
                self.con.commit()
                logging.debug("SAME CARDS")

        print("Your card has been created")
        print("Your card number:")
        print(card_number)
        print("Your card PIN:")
        print(pin)
        self.con.commit()

    # function used to calculate last digit of new credit card
    @staticmethod
    def calculate_control_sum(card_number):
        new_card = ""
        for index, single_digit in enumerate(card_number):
            index += 1
            if index % 2 != 0:
                if int(single_digit) * 2 > 9:
                    new_card += str(int(single_digit) * 2 - 9)
                else:
                    new_card += str(int(single_digit) * 2)
            else:
                new_card += single_digit
        control_number = sum(map(int, new_card))

        if control_number % 10 != 0:
            # control_number = control_number - control_number % 10 + 10
            control_number = 10 - control_number % 10
        else:
            control_number = 0
        card_number += str(control_number)
        return card_number

    # Handles menu when user wants to log in
    def menu_login_handle(self):
        print("Enter your card number:")
        card_entry = input()
        print("Enter your PIN")
        pin_entry = input()
        data = (card_entry, pin_entry)
        # check if user entered correct data
        # if card is in data base and pin is correct - log user

        sql_query_login = sql.SQL(
            "SELECT COUNT(id) FROM {table} WHERE {card_key} = %s AND {pin_key} = crypt(%s,{pin_key})").format(
            fields_viewed=sql.SQL(',').join([sql.Identifier('card_number'), sql.Identifier('pin'), ]),
            table=sql.Identifier(self.table_name),
            card_key=sql.Identifier(self.column_names["card_name"]),
            pin_key=sql.Identifier(self.column_names["pin_name"]), )

        self.cur.execute(sql_query_login, data)
        if self.cur.fetchone()[0] == 1:
            print("You have successfully logged in!")
            # set current user to card entry
            self.current_user = card_entry
            self.menu_login = False
        elif self.cur.fetchone() is None:
            print("Wrong card number or PIN!")
            self.menu_ = True
            self.menu_login = False

    # Handles menu when user is logged in
    def menu_logged_handle(self):

        def logged_in_add_income(balance_inner, sql_query_add_income_inner):
            print("Enter income:")
            income = input()
            try:
                income = int(income)
                if income <= 0:
                    print("Income cannot be equal or less than 0")
                else:
                    income_data = (income + balance_inner, self.current_user)
                    self.cur.execute(sql_query_add_income_inner, income_data)
                    self.con.commit()
            except ValueError:
                print("Value is not a number")

        def logged_in_do_transfer(balance_inner, sql_query_do_transfer_inner, sql_query_add_income_inner):
            print("Transfer")
            print("Enter card number:")
            card_transfer = input()
            # check card with luhn algorithm

            self.cur.execute(sql_query_do_transfer_inner, (card_transfer,))
            card_send = self.cur.fetchone()
            self.con.commit()
            logging.debug(f" card_send: {card_send}")
            logging.debug(f"calculated card: {self.calculate_control_sum(card_transfer)}")
            if self.calculate_control_sum(card_transfer)[-1] != "0":
                print("Probably you made a mistake in the card number. Please try again!")
            elif card_send:
                if card_send[0] == self.current_user:
                    print("You cannot transfer money to yourself")
                else:
                    print("Enter how much money you want to transfer:")
                    money_transfer = input()
                    try:
                        money_transfer = int(money_transfer)
                        if money_transfer <= 0:
                            print("Transfer cannot be equal of less than 0")
                        elif balance_inner - money_transfer < 0:
                            print("Not enough money!")
                        else:
                            money_minus = (balance_inner - money_transfer, self.current_user)
                            logging.debug(f"Money minus type: {type(money_minus)}")

                            money_plus = (money_transfer + card_send[1], card_send[0])

                            self.cur.execute(sql_query_add_income_inner, money_minus)
                            self.con.commit()
                            self.cur.execute(sql_query_add_income_inner, money_plus)
                            self.con.commit()
                            print("Success")

                    except ValueError:
                        print("Value is not an integer number")
            elif card_send is None:
                print("Such a card does not exist.")
            else:
                print("sth went wrong")

        # query when user wants to see balance
        sql_query_balance = sql.SQL("SELECT {fields_viewed} FROM {table} WHERE {card_key} = %s").format(
            fields_viewed=sql.Identifier(self.column_names["balance_name"]),
            table=sql.Identifier(self.table_name),
            card_key=sql.Identifier(self.column_names["card_name"]), )
        # query when user wants to add income, also used to transfer money between accounts
        sql_query_add_income = sql.SQL("UPDATE {table} SET {field} = %s WHERE {card_key} = %s").format(
            field=sql.Identifier(self.column_names["balance_name"]),
            table=sql.Identifier(self.table_name),
            card_key=sql.Identifier(self.column_names["card_name"]), )
        # query to view specific card and it's balance
        sql_query_do_transfer = sql.SQL("SELECT {fields_viewed} FROM {table} WHERE {card_key} = %s").format(
            fields_viewed=sql.SQL(',').join([sql.Identifier(self.column_names["card_name"]),
                                             sql.Identifier(self.column_names["balance_name"]), ]),
            table=sql.Identifier(self.table_name), card_key=sql.Identifier(self.column_names["card_name"]), )
        # query used to delete account
        sql_query_delete_account = sql.SQL("DELETE FROM {table} WHERE {card_key} = %s").format(
            table=sql.Identifier(self.table_name),
            card_key=sql.Identifier(self.column_names["card_name"]), )

        # download balance of current user
        self.cur.execute(sql_query_balance, (self.current_user,))
        balance = self.cur.fetchone()[0]

        # asks user as long as he chooses correct entry
        print("1. Balance", "2. Add Income", "3. Do transfer", "4. Close account", "5. Log out", "0. Exit", end="\n")
        choice = input()
        while choice not in self.menu_options_logged:
            print("Entry not recognized")
            print("1. Balance", "2. Add Income", "3. Do transfer", "4. Close account",
                  "5. Log out", "0. Exit", end="\n")
            choice = input()
        # prints balance
        if choice == "1":
            print(f"Balance: {balance}")
        # add income
        elif choice == "2":
            logged_in_add_income(balance, sql_query_add_income)
        # do transfer
        elif choice == "3":
            logged_in_do_transfer(balance, sql_query_do_transfer, sql_query_add_income)
        # close account
        elif choice == "4":
            self.cur.execute(sql_query_delete_account, (self.current_user,))
            self.con.commit()
            self.current_user = None
            self.menu_ = True
            print("The account has been closed!")
        # log out
        elif choice == "5":
            print("You have successfully logged out!")
            self.current_user = None
            self.menu_ = True
        # exit program
        elif choice == "0":
            self.menu_ = True
            self.menu_create_account = False
            self.menu_login = False
            self.current_user = None
            print("Bye!")
            sys.exit()
        else:
            print("Sth went wrong")


if __name__ == "__main__":
    logging.debug("Start of program")
    my_bank = Bank()
    my_bank.run_bank()

    logging.debug("End of program")
