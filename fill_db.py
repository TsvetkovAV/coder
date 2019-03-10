import psycopg2
import csv
import re
from src.utils import PATH, validate_row
from openpyxl import load_workbook
from src.normalize import normalize_desc

# create database puls;
# create user puls_user;
# grant all privileges on database puls to puls_user;

conn = psycopg2.connect(dbname='puls', host='localhost', user='puls_user', password='puls_user_pwd')
conn.autocommit = True
cursor = conn.cursor()

cursor.execute('Drop table puls;')
cursor.execute('CREATE TABLE puls ('
                   'CODE INTEGER UNIQUE NOT NULL, '
                   'DESCRIPTION TEXT NOT NULL,'
                   'N_DESCRIPTION TEXT NOT NULL,'
                   'FORM TEXT NOT NULL,'
                   'AMOUNT INTEGER NOT NULL,'
                   'DOSAGE TEXT NOT NULL,'
                   'MANUFACTURER TEXT NOT NULL, '
                   'PRIMARY KEY (code)'
               ');')


def run():
    # csv_data = csv.reader(open(PATH + '/data/puls_codes.csv'))
    # for row in csv_data:
    duplicates = 0
    train_data = [['description', 'manufacturer', 'correct_code', 'correct_desc', 'form', 'amount', 'dosage']]
    xlsx_data = load_workbook(PATH + '/src/data/full_codes.xlsx', read_only=True, data_only=True)
    for row in xlsx_data['Коды перекодировок'].rows:
        row = [cell.value for cell in row]
        if validate_row(row):
            try:
                code = int(row[3])
                if not row[6]:
                    duplicates += 1
                    continue
                else:
                    desc = re.sub("'", '', row[6])
                    orig_desc = desc
                if not row[7]:
                    manufacturer = ''
                else:
                    manufacturer = re.sub("'", '', row[7])

                if not row[4]:
                    duplicates += 1
                    continue
                else:
                    train_desc = re.sub("'", '', row[4])
                if not row[7]:
                    train_manufacturer = ''
                else:
                    train_manufacturer = re.sub("'", '', row[5])

                desc, desc_form, amount, dosage = normalize_desc(desc)

                train_row = [train_desc, train_manufacturer, code, desc, desc_form, amount, dosage]

            except Exception as exc:
                print(exc)
                return
            try:
                cursor.execute(
                    "INSERT INTO puls (CODE, DESCRIPTION, N_DESCRIPTION, FORM, AMOUNT, DOSAGE, MANUFACTURER) "
                    "VALUES ('%d', '%s', '%s', '%s', '%d', '%s', '%s');"
                    % (code, orig_desc, desc, desc_form, int(amount), dosage, manufacturer))
                train_data.append(train_row)
            except psycopg2.IntegrityError:
                # print("Duplicated value in puls - %d, %s, %s" % (code, desc, manufacturer))
                duplicates += 1

    print("Done")
    print("Duplicates =",duplicates)
    with open(PATH + '/src/data/train_data.csv', mode='w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in train_data:
            writer.writerow(row)
    cursor.close()
    conn.close()


if __name__ == '__main__':
    run()
