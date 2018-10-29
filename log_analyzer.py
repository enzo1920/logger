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
    "max_err": 30,
}


#декоратор время выполнения
def benchmark(original_func):
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = original_func(*args, **kwargs)
        end = datetime.datetime.now()
        print('{0} is executed in {1}'.format(original_func.__name__, end-start))
        return result
    return wrapper


#функция сравнения двух  максимальногозначения времени
#rel_tol - относительная толерантность, умножается на большую величину двух аргументов;
#по мере того как значения становятся больше, то и допустимая разность между ними при этом считается равной.
#abs_tol - абсолютный допуск, который применяется как-во всех случаях. 
#Если разница меньше любой из этих допусков, значения считаются равными. 
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    if(abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)):
     return b
    else:
     return a

#функция поиска медианы
def median(lst):
    n = len(lst)
    if n < 1:
            return None
    if n % 2 == 1:
            return sorted(lst)[n//2]
    else:
            return sum(sorted(lst)[n//2-1:n//2+1])/2.0
# на вход подавать имя файла
@benchmark
def reader():
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    error_counter=0#счетчик ошибок
    unique_urlcnt=0#счетчик уникальных урлов
    timetotal_url=0#счетчик уникальных урлов
    time_urls={}# словарь содержит url и время
    #rx = re.compile(r'(?:GET|POST)\s+(/\S+)')
    rx = re.compile(r'/\/(.*?)\/\?/ism')
    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
    print(file_log)
    if os.path.isfile(file_log):
     try:
       with gzip.open(file_log,'r') as gfile:
           lines_cnt = 0 #ограничемся пока 1000 строк
           for line in gfile:
                #ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line[:16] )
                finded =line.split(' ')
                #считаем согласно формату, что урл 7, если он не 7 значит формат менялся, очевидно нужно добавить регулярку , чтобы заматчить
                urls =finded[7].strip() #rx.findall(finded[7])
                time=float(line[-6:])
                #print(str(time)+' '+urls[0])

                #словарь статистики состоит из:time_url-время урла , url_count количества
                time_list=[] #список времени для урла,по нему будем считать медиану
                try:
                  #проверяем ли не пуст урл
                  if len(urls)!=0: 
                     if urls in time_urls:
                         time_list=time_urls[urls]['time_mass']
                         time_list.append(time)
                         time_urls.update({urls:
                                                 {"time_sum":time_urls[urls]['time_sum']+time,
                                                  "time_mass":time_list,
                                                  "cnt":time_urls[urls]["cnt"]+1}})
                         unique_urlcnt+=1

                     else:
                         time_list.append(time)
                         time_urls.update({urls:
                                                 {"time_sum":time,
                                                  "time_mass":time_list,
                                                  "cnt":1}})
                         #print(time_urls)

                  else:
                       print('url len=0')
                       error_counter+=1

                except Exception as exc:
                       #print(urls)
                       error_counter+=1
                       print(str(exc))
                lines_cnt+=1
                timetotal_url+=time
                if(lines_cnt==2000):
                   print(lines_cnt)
                   break

                  
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")

    else:
         print('file not found')
         time_urls={}
         error_counter=config["max_err"]
         unique_urlcnt=0,
         lines_cnt=0
         timetotal_url=0
    return time_urls,error_counter,unique_urlcnt,lines_cnt,timetotal_url


#функция для подсчета процентов на вход словарь с урлами и временем, на выходе словарь урл, время, процент процентами 
@benchmark
def percent_url_counter(dict,uniq_url,time_sum,err):
#считаем статистику для урла
    if(err<=config["max_err"]):
        for k,v in dict.iteritems():
               dict[k]["count_perc"]=100*float(dict[k]["cnt"])/float(uniq_url)
               dict[k]["time_perc"]=100*dict[k]["time_sum"]/float(time_sum)
               dict[k]["time_avg"]=dict[k]["time_sum"]/dict[k]["cnt"]
               #dict[k]["time_med"]=median(dict[k]["time list"])
               list_to_max=dict[k]["time_mass"]
               #максимум времени
               dict[k]["time_max"]=max(list_to_max)
               #медиана времени
               dict[k]["time_med"]=median(list_to_max)
    else:

        dict={}
        print("Много ошибок")
        #попробуем посчитать топ по 5 самым частым урлам
        #n = max(dict.values())
        #print range(n-10,n+1)[::-1]
    return dict

def main():
    #pass
    timeurls, errcnt,uniquecnt,total_cnt,total_time=reader()#получаем  словарЬ со значениями и количество ошибок при парсинге
    final_dict=percent_url_counter(timeurls,uniquecnt,total_time,errcnt)
    print("Error count is: "+str(errcnt))
    print("unique count  is: "+str(uniquecnt))
    print("total count str  is: "+str(total_cnt))
    print("total time url   is: "+str(total_time))
    #list=[0.3,0.155,0,0.112,0.8,0.1,0.2,4.7]
    for k,v in final_dict.iteritems():
        if(final_dict[k]["cnt"]>=2):
            print(k,v)


if __name__ == "__main__":
    main()
