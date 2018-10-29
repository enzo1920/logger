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
    "max_err": 700,
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


# на вход подавать имя файла
@benchmark
def reader():
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    error_counter=0#счетчик ошибок
    unique_urlcnt=0#счетчик уникальных урлов
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
                #print(finded[7])
                urls =finded[7].strip() #rx.findall(finded[7])
                time=float(line[-6:])
                #print(str(time)+' '+urls[0])

                #словарь статистики состоит из:time_url-время урла , url_count количества
                stat_dict={}
                try:
                   #ога тут оказывается, может быть пусто, занчит меняли формат
                  if len(urls)!=0: 
                     if urls in time_urls:
                         time_urls.update({urls:
                                                 {"time":time_urls[urls]['time']+time,
                                                   "cnt":time_urls[urls]["cnt"]+1}})
                         unique_urlcnt+=1
                         #print(urls)
                        #stat_dict["url_time"]=time#добавляем в словарь статистики время
                        #stat_dict["cnt"]=0#добавляем в словарь статистики количество 0
                        #time_urls["url"]=urls[0]
                        #time_urls["url"]=urls
                        #time_urls["stat"]=stat_dict #ключ- урл, значение- список со статистикой 
                     else:
                         time_urls.update({urls:
                                                 {"time":time,
                                                   "cnt":0}})
                         #print(time_urls)

                  else:
                       print('url len=0')
                       error_counter+=1
                    #print('error parsing url in str '+str(lines_cnt))
                    #print('error parsing url in str '+str(urls[0]))
                  #error_counter+=1
                  #print(time_urls)
                    #time_urls["url"]='/xxxxx'
                    #time_urls["time"]=0
                except Exception as exc:
                       #print(urls)
                       error_counter+=1
                       print(exc)
                lines_cnt+=1
                #if(lines_cnt==1000000):
                   #print(lines_cnt)
                   #break

                  
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")

    else:
         print('file not found')
         list_dict=0
    #print(list_dict)
    return time_urls,error_counter,unique_urlcnt,lines_cnt

# simple file counter
#def str_counter():
#    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
#    if os.path.isfile(file_log):
#       with gzip.open(file_log,'r') as gfile:
#           lines_cnt = 0 #ограничемся пока 1000 строк
#           for line in gfile:
#               lines_cnt+=1
#           print(lines_cnt)



#функция для подсчета процентов на вход словарь с абсолютными занчения abs_counter
@benchmark
def avg_counter(dict):
        #Пробуем посчитать средние значения
        urls_cnt=0
        for k,v in dict.iteritems():
             #print('unique url: '+str(urls_cnt))
             urls_cnt+=1
        #всего урл:
        print('totat distinct url: '+str(urls_cnt))
        #print(abs_dict)

        #for k,v in abs_dict.iteritems():
               #abs_dict[k]["percent_count"]=100*float(abs_dict[k]["cnt"])/float(urls_cnt)
        #print(abs_dict)

def main():
    pass
    #reader()
    timeurls, errcnt,uniquecnt,total_cnt=reader()#получаем список словарей со значениями и количество ошибок при парсинге
    #abs_dict=url_abscounter(lsturls,errcnt)
    #print(timeurls)
    print("Error count is: "+str(errcnt))
    print("uniquecnt  is: "+str(uniquecnt))
    print("total count str  is: "+str(total_cnt))

    #sys.exit()
    #print('Cnt Value: ',cnt)
    #print('Maximum Value: ',str(max))
    #print('Minimum Value: ',str(min))

    #str_counter()

if __name__ == "__main__":
    main()
