import datetime as dt
import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN_ILR')
HEADERS = {
    'Authorization': API_TOKEN,
    'Content-Type': 'application/json'
}
ALL_RESULTS_1000 = {}
ALL_RESULTS_5000 = {}


def set_sub20(row):
    dist = row['Dist']
    sec = row['Seconds']
    if dist == 1000:
        if sec < 180:
            return 'sub3'
        elif sec < 240:
            return 'sub4'
        elif sec < 300:
            return 'sub5'
        else:
            return ''
    elif dist == 5000:
        if sec < 1200:
                return 'sub20'
        elif sec < 1500:
            return 'sub25'
        else:
            return ''
    return ''


def set_results(row):
    name = row['name']
    dist = row['Dist']
    year = row['Year']
    data1000 = ALL_RESULTS_1000[year][0]
    data5000 = ALL_RESULTS_5000[year][0]
    try:
        if dist == 1000:
            return data1000.loc[data1000['name'] == name, 'index'].iloc[0]
        else:
            return data5000.loc[data5000['name'] == name, 'index'].iloc[0]
    except:
        return 'None'


def sub20(row):
    name = row['name']
    year = row['Year']
    dist = row['Dist']
    data1000 = ALL_RESULTS_1000[year][0]
    data5000 = ALL_RESULTS_5000[year][0]
    try:
        if dist == 1000:
            return data1000.loc[data1000['name'] == name, 's20'].iloc[0]
        else:
            return data5000.loc[data5000['name'] == name, 's20'].iloc[0]
    except:
        return ''


def set_results_gender(row):
    name = row['name']
    dist = row['Dist']
    gender = row['gender']
    year = row['Year']

    if dist == 1000:
        data_m = ALL_RESULTS_1000[year][1]
        data_w = ALL_RESULTS_1000[year][2]
    else:
        data_m = ALL_RESULTS_5000[year][1]
        data_w = ALL_RESULTS_5000[year][2]

    if gender == 'М':
        return data_m.loc[data_m['name'] == name, 'index'].iloc[0]
    else:
        return data_w.loc[data_w['name'] == name, 'index'].iloc[0]


def define_progress(data):
    res = []
    for i in range(11, 0, -1):
        if data[i] == 0:
            res.append(0)
        else:
            if data[i-1] != 0:
                if data[i] < data[i-1]:
                    res.append(1)
                elif data[i] == data[i-1]:
                    res.append(0)
                else:
                    res.append(-1)
            else:
                k = i - 1
                if i == 9:
                    b = 1
                while data[k] == 0 and k > 0:
                    k -= 1
                if data[k] == 0:
                    res.append(0)
                else:
                    if data[i] < data[k]:
                        res.append(1)
                    elif data[i] == data[k]:
                        res.append(0)
                    else:
                        res.append(-1)
    res.append(0)
    return list(reversed(res))


def delete_data_from_server_ilr():
    url = 'http://51.250.80.45:8000/running-api/v1/drop-results/'
    requests.request("DELETE", url, headers=HEADERS, data={})


def upload_data_to_server_ilr(data):
    url = 'http://51.250.80.45:8000/running-api/v1/results/'
    try:
        requests.request("POST", url, headers=HEADERS,
                         data=json.dumps(data['results'][0:1500]))
        if len(data['results']) > 1500:
            requests.request("POST", url, headers=HEADERS,
                             data=json.dumps(data['results'][1500:3000]))
        if len(data['results']) > 3000:
            requests.request("POST", url, headers=HEADERS,
                             data=json.dumps(data['results'][3000:4500]))
    except requests.exceptions.Timeout:
        raise Exception('Сервер отвалился по таймауту')
    except requests.exceptions.RequestException:
        raise Exception('Что-то не так с запросом к серверу')
    except requests.exceptions.ConnectionError:
        raise Exception('Не удалось соедениться с сайтом Яндекс.Практикум')
    except requests.exceptions.InvalidHeader:
        raise Exception('Ошибка в Header')
    except requests.exceptions.InvalidURL:
        raise Exception('Неаверно сформирована ссылка')
    except TypeError:
        raise Exception('Не удалось преобразовать ответ в JSON')
    except ValueError:
        raise Exception('Не удалось преобразовать ответ в JSON (Value error)')
    except Exception as e:
        raise Exception(e)


def transform_data_ilr(data):
    df = data.copy()
    df = df[df['name'] != '']
    df['date'] = df['date'].apply(
        lambda x: dt.datetime.strptime(x, '%d.%m.%Y'))
    df['Year'] = pd.DatetimeIndex(df['date']).year
    df['Dist'] = df['Dist'].astype('int32')
    df = df[df['Year'] >= 2021]

    df['place'] = df.apply(set_results, axis=1)
    df['sub20'] = df.apply(sub20, axis=1)
    df['m/w'] = df.apply(set_results_gender, axis=1)

    df['name'] = df['name'].apply(lambda x: x.split()[1] + ' ' + x.split()[0])
    d = df[['name', 'date']]
    i = 0
    for row in d[d.duplicated()].values:
        data = df[(df['name'] == row[0]) & (df['date'] == row[1])].sort_values(by='Seconds').iloc[0:1]
        # display(data)
        # display(df[(df['name'] == row[0]) & (df['date'] == row[1])])
        df = df.drop(index=df[(df['name'] == row[0]) & (df['date'] == row[1])].index)
        df = pd.concat([df, data])

    df['year'] = pd.DatetimeIndex(df['date']).year
    df['month'] = pd.DatetimeIndex(df['date']).month

    result = {'results': []}
    for col, data in df[df['Dist'] == 1000].groupby(['name', 'year']):
        jan = '0'
        feb = '0'
        mar = '0'
        apr = '0'
        may = '0'
        jun = '0'
        jul = '0'
        aug = '0'
        sep = '0'
        oct = '0'
        nov = '0'
        dec = '0'

        res_month = [0] * 12
        for i in range(len(data)):
            val = str(data.values[i][2])
            res_month[data.values[i][12] - 1] = data.values[i][6]
            if data.values[i][12] == 1:
                jan = val
            if data.values[i][12] == 2:
                feb = val
            if data.values[i][12] == 3:
                mar = val
            if data.values[i][12] == 4:
                apr = val
            if data.values[i][12] == 5:
                may = val
            if data.values[i][12] == 6:
                jun = val
            if data.values[i][12] == 7:
                jul = val
            if data.values[i][12] == 8:
                aug = val
            if data.values[i][12] == 9:
                sep = val
            if data.values[i][12] == 10:
                oct = val
            if data.values[i][12] == 11:
                nov = val
            if data.values[i][12] == 12:
                dec = val

        res_month = define_progress(res_month)
        rank = 'none'
        best_time_sec = data[data['Seconds'] == data['Seconds'].min()].values[0][6]
        dist = data.values[0][1]
        if data.values[0][1] == 1000:
            if best_time_sec < 180:
                rank = 'SUB3'
            elif best_time_sec < 240:
                rank = 'SUB4'
            elif best_time_sec < 300:
                rank = 'SUB5'
        elif data.values[0][1] == 5000:
            if best_time_sec < 1200:
                rank = 'SUB20'
            elif best_time_sec < 1500:
                rank = 'SUB25'

        row = {
            'overall_place': str(data.values[0][8]),
            'place_in_group': data.values[0][10],
            'name': data.values[0][0],
            'distance': data.values[0][1],
            'result': 0,
            'best_time': str(data.sort_values(by='Seconds').values[0][2]),
            'city': data.values[0][4],
            'gender': data.values[0][5],
            'rank': rank,
            'year': str(data.values[0][7]),
            'jan_result': str(jan),
            'feb_result': str(feb),
            'mar_result': str(mar),
            'apr_result': str(apr),
            'may_result': str(may),
            'jun_result': str(jun),
            'jul_result': str(jul),
            'aug_result': str(aug),
            'sep_result': str(sep),
            'oct_result': str(oct),
            'nov_result': str(nov),
            'dec_result': str(dec),
            'jan_progress': res_month[0],
            'feb_progress': res_month[1],
            'mar_progress': res_month[2],
            'apr_progress': res_month[3],
            'may_progress': res_month[4],
            'jun_progress': res_month[5],
            'jul_progress': res_month[6],
            'aug_progress': res_month[7],
            'sep_progress': res_month[8],
            'oct_progress': res_month[9],
            'nov_progress': res_month[10],
            'dec_progress': res_month[11]
        }
        result['results'].append(row)

    for col, data in df[df['Dist'] == 5000].groupby(['name', 'year']):
        jan = '0'
        feb = '0'
        mar = '0'
        apr = '0'
        may = '0'
        jun = '0'
        jul = '0'
        aug = '0'
        sep = '0'
        oct = '0'
        nov = '0'
        dec = '0'

        res_month = [0] * 12
        for i in range(len(data)):
            val = str(data.values[i][2])
            res_month[data.values[i][12] - 1] = data.values[i][6]
            if data.values[i][12] == 1:
                jan = val
            if data.values[i][12] == 2:
                feb = val
            if data.values[i][12] == 3:
                mar = val
            if data.values[i][12] == 4:
                apr = val
            if data.values[i][12] == 5:
                may = val
            if data.values[i][12] == 6:
                jun = val
            if data.values[i][12] == 7:
                jul = val
            if data.values[i][12] == 8:
                aug = val
            if data.values[i][12] == 9:
                sep = val
            if data.values[i][12] == 10:
                oct = val
            if data.values[i][12] == 11:
                nov = val
            if data.values[i][12] == 12:
                dec = val

        res_month = define_progress(res_month)
        rank = 'none'
        best_time_sec = data[data['Seconds'] == data['Seconds'].min()].values[0][6]
        dist = data.values[0][1]
        if data.values[0][1] == 1000:
            if best_time_sec < 180:
                rank = 'SUB3'
            elif best_time_sec < 240:
                rank = 'SUB4'
            elif best_time_sec < 300:
                rank = 'SUB5'
        elif data.values[0][1] == 5000:
            if best_time_sec < 1200:
                rank = 'SUB20'
            elif best_time_sec < 1500:
                rank = 'SUB25'

        row = {
            'overall_place': str(data.values[0][8]),
            'place_in_group': data.values[0][10],
            'name': data.values[0][0],
            'distance': data.values[0][1],
            'result': 0,
            'best_time': str(data.sort_values(by='Seconds').values[0][2]),
            'city': data.values[0][4],
            'gender': data.values[0][5],
            'rank': rank,
            'year': str(data.values[0][7]),
            'jan_result': str(jan),
            'feb_result': str(feb),
            'mar_result': str(mar),
            'apr_result': str(apr),
            'may_result': str(may),
            'jun_result': str(jun),
            'jul_result': str(jul),
            'aug_result': str(aug),
            'sep_result': str(sep),
            'oct_result': str(oct),
            'nov_result': str(nov),
            'dec_result': str(dec),
            'jan_progress': res_month[0],
            'feb_progress': res_month[1],
            'mar_progress': res_month[2],
            'apr_progress': res_month[3],
            'may_progress': res_month[4],
            'jun_progress': res_month[5],
            'jul_progress': res_month[6],
            'aug_progress': res_month[7],
            'sep_progress': res_month[8],
            'oct_progress': res_month[9],
            'nov_progress': res_month[10],
            'dec_progress': res_month[11]
        }
        result['results'].append(row)
    return result
