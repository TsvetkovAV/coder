import csv
import pymysql
import re
from src.utils import PATH, validate_row
from src.normalize import normalize_desc
import warnings

db = pymysql.connect(host='127.0.0.1',
                             port=9306,
                             user='',
                             passwd='',
                             db='',
                             cursorclass=pymysql.cursors.DictCursor)


def Mg_to_mg(match):
    value = float(match.group(1) + '.' + match.group(3)) * 1000
    if value % 1 == 0:
        value = int(value)
    return match.group(2).join(str(value).split('.'))


def run():
    cursor = db.cursor(pymysql.cursors.DictCursor)
    data = open(PATH + '/src/data/train_data.csv')
    csv_data = csv.reader(data)
    for i in range(4):
        data.seek(0)
        fails = 0
        wins = 0
        for row in csv_data:
            if validate_row(row):
                train_desc = row[0]
                train_manuf = row[1]
                correct_code = row[2]
                # N90 -> х90
                train_desc = re.sub('N(\d+)', r'х\1', train_desc)
                # 2.0 -> 2
                train_desc = re.sub('(\d+)[,.]0([\D$])', r'\1\2', train_desc)
                # 0.005 -> 5
                train_desc = re.sub('(\d+)([,.])(\d+)', Mg_to_mg, train_desc)

                n_train_desc, desc_form, amount, dosage = normalize_desc(train_desc)

                train_desc = re.sub('[^\da-zа-я,.\s%]', ' ', train_desc.lower())
                query = ' | '.join(train_desc.split())
                try:
                    if i == 0:
                        cursor.execute(
                            "Select *, WEIGHT() from puls_index "
                            "where MATCH('@description \""+train_desc+"\"/0.2 @description "+query+"') "
                            "limit 10 OPTION ranker=expr('bm25')"
                        )
                    elif i == 1:
                        cursor.execute(
                            "Select *, WEIGHT() from puls_index "
                            "where amount = "+amount+" and MATCH('"
                                "@description \""+train_desc+"\"/0.2 @description "+query+
                            "') limit 10 OPTION ranker=expr('bm25')"
                        )
                    elif i == 2:
                        if dosage == '':
                            dosage_q = ''
                        else:
                            dosage_q = "@dosage \""+dosage+"\"/0.2 "
                        cursor.execute(
                            "Select *, WEIGHT() from puls_index "
                            "where amount = "+amount+" and MATCH('"
                                "@description \""+train_desc+"\"/0.2 @description "+query+" " + dosage_q +
                            "') limit 10 OPTION ranker=expr('bm25')"
                        )
                    elif i == 3:
                        if dosage == '':
                            dosage_q = ''
                        else:
                            dosage_q = "@dosage \""+dosage+"\"/0.2 "
                        if desc_form == '':
                            desc_form_q = ''
                        else:
                            desc_form_q = "@form \""+desc_form+"\"/0.2 "
                        cursor.execute(
                            "Select *, WEIGHT() from puls_index "
                            "where amount = "+amount+" and MATCH('"
                                "@description \""+train_desc+"\"/0.2 @description "+query+" " + dosage_q + desc_form_q +
                            "') limit 10 OPTION ranker=expr('bm25')"
                        )
                except Exception as exc:
                    print(exc)
                result = cursor.fetchall()

                if (len(result) == 0) or (int(correct_code) not in [res['code'] for res in result]):
                    fails += 1
                elif result[0]['code'] == int(correct_code):
                    wins += 1

        print('Fails -', fails, '('+str(round(fails/10138, 3))+')')
        print('Wins -', wins, '('+ str(round(wins/10138, 3))+')')
        print('i -',i)


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    run()
