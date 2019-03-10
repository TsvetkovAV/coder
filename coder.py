import psycopg2
from difflib import get_close_matches
import csv
from src.utils import PATH, validate_row

conn = psycopg2.connect(dbname='puls', host='localhost', user='puls_user')
conn.autocommit = True
cursor = conn.cursor()


csv_data = csv.reader(open(PATH + '/data/train_data.csv'))
fails = 0
i = 1
for row in csv_data:
    if validate_row(row):
        i += 1
        if i%100==0:
            print(i//100)
        zdrav_name = row[0]
        correct_code = row[2]

        cursor.execute("Select code, description from puls")
        as_dict = {row[1]: row[0] for row in cursor.fetchall()}
        descriptions = as_dict.keys()

        result = get_close_matches(zdrav_name, descriptions, 1, 0)
        if len(result) == 0:
            print('Could not find appropriate code -',zdrav_name)
            fails += 1
            continue
        if as_dict[result[0]] != correct_code:
            fails += 1
print(fails)
