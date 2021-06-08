Description:
Hyperskill project implementing banking system with use of PostgreSQL (psycopg2 extension).
User has possibility to create an account (with use of terminal console). When it’s done he obtains unique credit card number starting with “4000000” and ended with randomized numbers but the whole credit card number has to match “Luhn algorithm”. PIN is also randomized, crypted and inserted into the database.
After logging in user can check the balance of the account, add income, make a transfer to another user by giving his credit card number, closing account, logging out and shutting down the program.
