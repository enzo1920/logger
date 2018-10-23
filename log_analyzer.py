#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import gzip
import os
import datetime
import time
import sys
#import gc
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "max_err": 115,
}



# на вход подавать имя файла
def reader():
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    error_counter=0#счетчик ошибок
    list_dict=[]#список со словарями
    rx = re.compile(r'(?:GET|POST)\s+(/\S+)')
    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
    print(file_log)
    if os.path.isfile(file_log):
     try:
       with gzip.open(file_log,'r') as gfile:
           lines_cnt = 0 #ограничемся пока 1000 строк
           for line in gfile:
                ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line[:16] )
                urls = rx.findall(line)
                time=float(line[-6:])
                #print(str(time)+' '+urls[0])
                time_urls={}# словарь содержит url и время
                #словарь статистики состоит из:time_url-время урла , url_count количества
                stat_dict={}
                try:
                   #ога тут оказывается, может быть пусто, занчит меняли формат
                  if len(urls)!=0:
                    stat_dict["url_time"]=time#добавляем в словарь статистики время
                    stat_dict["cnt"]=0#добавляем в словарь статистики количество 0
                    time_urls["url"]=urls[0]
                    time_urls["stat"]=stat_dict #ключ- урл, значение- список со статистикой 
                  else:
                    print('error parsing url in str '+str(lines_cnt))
                    error_counter+=1
                    #time_urls["url"]='/xxxxx'
                    #time_urls["time"]=0
                except Exception as exc:
                       #print(urls)
                       print(str(len(urls)))
                list_dict.append(time_urls)
                lines_cnt+=1
                if(lines_cnt==100):
                   print(lines_cnt)
                   break

                  
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")

    else:
         print('file not found')
         list_dict=0
    #print(list_dict)
    return list_dict,error_counter

# simple file counter
#def str_counter():
#    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
#    if os.path.isfile(file_log):
#       with gzip.open(file_log,'r') as gfile:
#           lines_cnt = 0 #ограничемся пока 1000 строк
#           for line in gfile:
#               lines_cnt+=1
#           print(lines_cnt)


#декоратор время выполнения
def time_decorator(original_func):
    print('---begin---->')
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = original_func(*args, **kwargs)
        end = datetime.datetime.now()
        print('{0} is executed in {1}'.format(original_func.__name__, end-start))
        return result
    return wrapper


#Функция подсчета статистики по url'ам. На вход подается лист словарей list[{"url":url},{"time":time}]
@time_decorator
def url_abscounter(list_urls, err_cnt):
    lines_cnt= 0 #ограничемся пока 1000 строк
    max_val=0 # максимальное значение урлов
    min_val=0 # минимальное значение урлов
    dict_absstat={}#словарь, в который будем записывать суммарное количество вхождений урлов
    print('config max error is: '+str(config['max_err'])+' analysis error is: '+str(err_cnt))
    if(err_cnt<=config['max_err']):
          for dict_row in list_urls:# получается , что у нас каждая строчка словарь
              try:
                 #print(dict_row["stat"] )
                 if dict_row["url"] in dict_absstat:#.keys():
                                  print("find!!!!")
                                  #time.sleep(5)
                                  dict_absstat.update({dict_row["url"]:
                                                       {"time":dict_absstat["time"]+dict_row["stat"]["url_time"],
                                                        "cnt":dict_absstat["cnt"]+1,
                                                        "min":min([dict_absstat[dict_row["url"]]],dict_absstat["min"]),
                                                        "max":max([dict_absstat[dict_row["url"]]],dict_absstat["max"])}})

                 else:
                                  #print("2")
                      dict_absstat.update({dict_row["url"]:
                                                           {"time":dict_row["stat"]["url_time"],
                                                           "cnt":1,
                                                           "min":dict_row["stat"]["url_time"],
                                                           "max":dict_row["stat"]["url_time"]}})
                      #dict_row["stat"]["cnt"]=1
                      #print(dict_row["stat"]["cnt"])

                      #dict_absstat[row["url"]]=1
                 lines_cnt+=1
              except Exception as exc:
                       print('-----error count in -->> '+str(exc))
          #пробуем посчитать максимум и минимум из словарями
          #key_max = max(dict_absstat.keys(), key=(lambda k: dict_absstat[k]))
          #key_min = min(dict_absstat.keys(), key=(lambda k: dict_absstat[k]))
          #max_val=dict_absstat[key_max]
          #min_val=dict_absstat[key_min]
          #print('Cnt Value: ',str(lines_cnt))
          #print('Maximum Value: ',str(max_val))
          #print('Minimum Value: ',str(min_val))
          #print(dict_absstat)
    else:   
          print('Analysis: your file contins more errors than set in config')
          print(lines_cnt)
    print(dict_absstat["url"]["cnt"])
    #return  dict_absstat


def main():
    #pass
    #max,min,cnt=
    lsturls, errcnt=reader()#получаем список словарей со значениями и количество ошибок при парсинге
    url_abscounter(lsturls,errcnt)

    #sys.exit()
    #print('Cnt Value: ',cnt)
    #print('Maximum Value: ',str(max))
    #print('Minimum Value: ',str(min))

    #str_counter()

if __name__ == "__main__":
    main()
