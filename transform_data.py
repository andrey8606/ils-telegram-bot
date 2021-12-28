import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime
import time
from dotenv import load_dotenv


load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
HEADERS = {
    'Authorization': 'Token ' + API_TOKEN,
    'Content-Type': 'application/json'
}
ALL_RESULTS = {}


def set_sub20(sec):
    if sec < 960:
        return 'sub16'
    elif sec < 1080:
        return 'sub18'
    elif sec < 1200:
        return 'sub20'
    else:
        return ''


def set_results(row):
    name = row['name']
    dist = row['Dist']
    year = row['Year']
    # это верно только для 1000м, для 100м - дописать, когда появится информация
    data1000 = ALL_RESULTS[year][0]
    data100 = ALL_RESULTS[year][0]
    try:
        if dist == 100:
            return data100.loc[data100['name'] == name, 'index'].iloc[0]
        else:
            return data1000.loc[data1000['name'] == name, 'index'].iloc[0]
    except:
        return 'None'


def sub20(row):
    name = row['name']
    year = row['Year']
    data1000 = ALL_RESULTS[year][0]
    try:
        return data1000.loc[data1000['name'] == name, 's20'].iloc[0]
    except:
        return ''


def set_results_gender(row):
    name = row['name']
    dist = row['Dist']
    gender = row['gender']
    year = row['Year']

    data_m = ALL_RESULTS[year][1]
    data_w = ALL_RESULTS[year][2]

    if gender == 'М':
        if dist == 1000:
            return data_m.loc[data_m['name'] == name, 'index'].iloc[0]
    else:
        if dist == 1000:
            return data_w.loc[data_w['name'] == name, 'index'].iloc[0]


def define_progress(data):
    res = []
    for i in range(11, 0, -1):
        if data[i] == 0:
            res.append(0)
        else:
            if data[i - 1] != 0:
                if data[i] < data[i - 1]:
                    res.append(1)
                elif data[i] == data[i - 1]:
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


def delete_data_from_server():
    url = 'https://league.ilovesupersport.com/swimming-api/v1/drop-results/'
    response = requests.request("DELETE", url, headers=HEADERS, data={})


def upload_data_to_server(data):
    url = 'https://league.ilovesupersport.com/swimming-api/v1/results/'
    try:
        response = requests.request("POST", url, headers=HEADERS, data=json.dumps(data['results'][0:1000]))
        response = requests.request("POST", url, headers=HEADERS, data=json.dumps(data['results'][1000:2000]))
        response = requests.request("POST", url, headers=HEADERS, data=json.dumps(data['results'][2000:3000]))
        response = requests.request("POST", url, headers=HEADERS, data=json.dumps(data['results'][3000:]))
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


def transform_data(data):
    df = data.copy()
    df['Year'] = pd.DatetimeIndex(df['date']).year
    df = df[df['Year'] != 2015]

    for col, data in df.groupby('Year'):
        res1000 = (data[data['Dist'] == 1000]
                   .pivot_table(index='name', values='Seconds', aggfunc='min')
                   .sort_values(by='Seconds')
                   .reset_index().reset_index())
        res1000['index'] = res1000['index'].apply(lambda x: x + 1)
        res1000['s20'] = res1000['Seconds'].apply(set_sub20)

        res_m_1000 = (data[(data['Dist'] == 1000) & (data['gender'] == 'М')]
                      .pivot_table(index='name', values='Seconds', aggfunc='min')
                      .sort_values(by='Seconds').reset_index().reset_index())
        res_m_1000['index'] = res_m_1000['index'].apply(lambda x: x + 1)
        res_w_1000 = (data[(data['Dist'] == 1000) & (data['gender'] == 'Ж')]
                      .pivot_table(index='name', values='Seconds', aggfunc='min')
                      .sort_values(by='Seconds').reset_index().reset_index())
        res_w_1000['index'] = res_w_1000['index'].apply(lambda x: x + 1)

        ALL_RESULTS[col] = [res1000, res_m_1000, res_w_1000]

    df['place'] = df.apply(set_results, axis=1)
    df['sub20'] = df.apply(sub20, axis=1)
    df['m/w'] = df.apply(set_results_gender, axis=1)
    df['name'] = df['name'].apply(lambda x: x.split()[1] + ' ' + x.split()[0])

    d = df[['name', 'date']]
    i = 0
    for row in d[d.duplicated()].values:
        data = df[(df['name'] == row[0]) & (df['date'] == row[1])].sort_values(by='Seconds').iloc[0:1]
        df = df.drop(index=df[(df['name'] == row[0]) & (df['date'] == row[1])].index)
        df = pd.concat([df, data])

    df['year'] = pd.DatetimeIndex(df['date']).year
    df['month'] = pd.DatetimeIndex(df['date']).month

    result = {'results': []}
    for col, data in df.groupby(['name', 'year']):
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
        best_time_sec = data[data['Seconds'] == data['Seconds'].min()].values[0][6]
        if best_time_sec < 960:
            rank = 'SUB16'
        elif best_time_sec < 1080:
            rank = 'SUB18'
        elif best_time_sec < 1200:
            rank = 'SUB20'
        else:
            rank = 'none'

        row = {
            'overall_place': data.values[0][8],
            'place_in_group': data.values[0][10],
            'name': data.values[0][0],
            'distance': data.values[0][1],
            'result': 0,
            'best_time': str(data.sort_values(by='Seconds').values[0][2]),
            'city': data.values[0][4],
            'gender': data.values[0][5],
            'pool_type': '50 meters',
            'rank': rank,
            'year': data.values[0][7],
            'jan_result': jan,
            'feb_result': feb,
            'mar_result': mar,
            'apr_result': apr,
            'may_result': may,
            'jun_result': jun,
            'jul_result': jul,
            'aug_result': aug,
            'sep_result': sep,
            'oct_result': oct,
            'nov_result': nov,
            'dec_result': dec,
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
