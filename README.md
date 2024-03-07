Add your telegram token to config.py

About bot:


This Telegram bot serves as a questionnaire platform where users are prompted with questions and are required to provide answers within a specified time frame. 
The bot is implemented in Python using the Aiogram library for interacting with the Telegram Bot API and SQLite for database management.

Overview:

Bot Initialization:

The bot is initialized with a Telegram API token obtained from the BotFather.
A dispatcher (dp) is created to manage message handlers.
A router (router) is used to define message handling routes.

Handlers:

The bot has several command handlers:

/start: Initiates the conversation, prompting users to enter their first name and last name.
/restart: Allows users to restart the questionnaire.
/admin: Sets the chat ID for administrative purposes.
/data: Retrieves and sends all user answers as a document.

Questionnaire Workflow:
Upon starting the conversation, users are prompted to enter their full name.
User data (ID, name, nickname) is stored in an SQLite database, and a set of questions is loaded from an input file.
Users are asked to press "Enter" to begin the questionnaire.
Questions are presented sequentially to the user, and they have a set time to respond.
The bot notifies users when time is running out.
User answers are stored in the database.
Once all questions are answered, a document containing all responses is generated and sent.

Database Management (SQLite):
Two tables (users and answers) are created to store user information and responses.
The add_users_db method adds user data to the users table.
The add_answers_db method adds user responses to the answers table using the executemany method for efficiency.
The fetch_all method retrieves all user data and answers, joining the two tables.

File Handling:
The input_file function reads a text file containing questions and durations, extracting and formatting the data.
The output_word_file function generates a Word document with individual user answers.
The output_all_data_file function creates a Word document with answers from all users.

Configuration and Constants:
Various constants such as buttons, timers, and waiting times are defined in global_vars.py.
Configuration settings, such as the Telegram API token, are stored in the config.py file.

Conclusion:
This Telegram bot facilitates a structured questionnaire experience for users, managing their responses and generating comprehensive reports. 
It employs asynchronous programming to handle user interactions efficiently and integrates file handling and SQLite for persistent data storage. 
The modular design makes it extensible and adaptable for future enhancements.
