import csv
import pymysql
import re
from src.utils import PATH, validate_row
from difflib import get_close_matches
from src.normalize import normalize_desc

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
    return match.group(2).join(str(value).split('.')) + ' мг'


def group_sub_function(m):
    global word_found
    global word_sub
    if not word_found:
        word_found = True
        return m.group(1)+word_sub


global word_found
global word_sub
cursor = db.cursor(pymysql.cursors.DictCursor)
data = open(PATH + '/src/data/train_data.csv')
csv_data = csv.reader(data)
# for i in ['sum(lcs*user_weight)*1000+bm25', 'bm25', '1', 'sum(hit_count*user_weight)', 'sum(lcs*user_weight)',
#           'sum((word_count+(lcs-1)*max_lcs)*user_weight)', 'field_mask',
#           'sum((4*lcs+2*(min_hit_pos==1)+exact_hit)*user_weight)*1000+bm25']:
# for i in [0.2, 0.4, 0.6, 0.8]:
for i in [0.2]:
    data.seek(0)
    fails = 0
    wins = 0
    for row in csv_data:
        if validate_row(row):
            train_desc = row[0]
            train_manuf = row[1]
            correct_code = row[2]

            train_manuf = re.sub('[.,()+"\']+', '', train_manuf).strip()

            # Bring to Puls format
            # N90 -> х90
            train_desc = re.sub('N(\d+)', r'х\1', train_desc)
            # 2.0 -> 2
            train_desc = re.sub('(\d+)[,.]0([\D$])', r'\1\2', train_desc)
            # 0.005 -> 5 мг
            train_desc = re.sub('(\d+)([,.])(\d+)', Mg_to_mg, train_desc)

            train_desc, desc_form, amount, dosage = normalize_desc(train_desc)

            form_query = desc_form.split(' ')
            if len(form_query) > 1:
                form_query = '"'+' | '.join(form_query)+'"'
            else:
                form_query = form_query[0]

            train_desc = re.sub('[^\da-zа-я,.\s%]', ' ', train_desc)

            try:
                query = "Select *, WEIGHT() from puls_index "\
                            "where amount = "+amount+" and MATCH('"\
                            "@form \""+desc_form+"\"/0.2 "\
                            "@dosage \""+dosage+"\"/0.2 "\
                            "@description \""+train_desc+"\"/0.2 ') "\
                        "limit 5 OPTION ranker=expr('bm25')"
                # print(query)
                cursor.execute(query)
            except Exception as exc:
                print(exc)
            result = cursor.fetchall()

            if len(result) == 0:
                fails += 1
                continue
            if int(correct_code) in [res['code'] for res in result]:
                if result[0]['code'] == int(correct_code):
                    wins += 1
            else:
                # print(row[0], '-----', train_desc, '-----', row[3])
                fails += 1
    print(fails, 'fails('+str(round(fails/10138, 3))+') with i =', str(i))
    print('Wins -', wins, '('+str(round(wins/10138, 3))+')')
