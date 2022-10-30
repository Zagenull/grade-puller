# grade-puller
Python 3.10 productivity script for pulling assignments from various platforms and putting them with due dates on Trello

This script uses TrelloAPI and BS4 to scrape for a login box to Gradescope, Sakai, or MyMathLab and login with the provided user-pass.

The program will then take from the links within courseSakai.txt and the course codes within courseGradescope.txt to find all of their assignment with due dates, pushing them to the Trello board of the inputted API key.

Exceptions can be added to exceptions.txt
