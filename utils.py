import os
import re

PATH = os.getcwd()


def validate_row(current_row):
    if ('Код ПУЛЬС' not in current_row) and ('description' not in current_row):
       return True
    else:
        return False


