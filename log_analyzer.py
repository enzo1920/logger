#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import gzip
import os
import datetime
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}



# на вход подавать имя файла
def reader():
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    
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
                try:
                   #ога тут оказывается, может быть пусто, занчит меняли формат
                  if len(urls)!=0:
                    time_urls["url"]=urls[0]
                    time_urls["time"]=time
                  else:
                    time_urls["url"]='/xxxxx'
                    time_urls["time"]=0
                except Exception as exc:
                       #print(urls)
                       print(str(len(urls)))
                list_dict.append(time_urls)
                lines_cnt+=1
                if(lines_cnt==500000):
                   print(lines_cnt)
                   break

                  
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")

    else:
         print('file not found')
         list_dict=0
    return list_dict

# simple file counter
def str_counter():
    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
    if os.path.isfile(file_log):
       with gzip.open(file_log,'r') as gfile:
           lines_cnt = 0 #ограничемся пока 1000 строк
           for line in gfile:
               lines_cnt+=1
           print(lines_cnt)


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
def url_abscounter():
    list_urls=reader()#получаем список словарей со значениями
    dict_absstat={} 
    lines_cnt= 0 #ограничемся пока 1000 строк
    for row in list_urls:
        try:
         if row["url"] in dict_absstat.keys():
              dict_absstat[row["url"]]+=1
         else:
            dict_absstat[row["url"]]=1
         lines_cnt+=1
        except Exception as exc:
                 print('-----error-->>'+str(line_err))
    #пробуем посчитать максимум и миниму из словарями
    key_max = max(dict_absstat.keys(), key=(lambda k: dict_absstat[k]))
    key_min = min(dict_absstat.keys(), key=(lambda k: dict_absstat[k]))
    print(lines_cnt)
    print('Maximum Value: ',dict_absstat[key_max])
    print('Minimum Value: ',dict_absstat[key_min])
     #print(dict_absstat)



def main():
    #pass
    url_abscounter()
    #str_counter()

if __name__ == "__main__":
    main()
