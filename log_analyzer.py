#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import gzip
import os
import datetime
import time
import sys
import json
from string import Template
#import gc
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 20,
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

#функция проверки существования файла отчета
def check_report(report_dir,date_stamp):
    file_report_rend=report_dir+'/report-'+date_stamp.strftime("%Y.%m.%d")+'.html' #файл который рендерим, отчет
    
    if os.path.exists(file_report_rend):
         print('File is alive  '+file_report_rend)
         return True 
    else:
         print('{0} func : file not found {1}'.format(sys._getframe().f_code.co_name,file_report_rend))
         #print('File not found  '+file_report_rend)
         return False 


#функция открытия файла гзип или плейн
def openfile(filename,file_ext, mode='r'):
    if (file_ext=='gz'):
        return gzip.open(filename, mode) 
    else:
        return open(filename, mode)

#функция поиска самого свежего лога
def log_finder(log_dir):
    files = os.listdir(log_dir)
    dict_files={}
    #какие расширения файла будем открывать
    ext_list=['gz','plain']
    for name in files:
         split_names=name.split('.')
         # предпологаем, что формат имени будет такой. $service_name $log_name $ext 
         #nginx-access-ui.log-20170630.gz
         #все это разделено точками 
         #dictionary {service:{date:ext}}

         try:
              extract_date=datetime.datetime.strptime(split_names[1][4:], '%Y%m%d')
              year=extract_date.year
              month='{:02d}'.format(extract_date.month)
              day='{:02d}'.format(extract_date.day)
              str_date=str(year)+'.'+str(month)+'.'+str(day)
              if(len(split_names)>2):
                  print(split_names[0]+' has date: '+str_date+' ext is:'+split_names[2])
                  #dict_files.update({})
                  file_ext=split_names[2]
              else:
                  print(split_names[0]+' has date: '+str_date+' ext not found. plain ')
                  file_ext='plain'
              #в словарь пойдут только логи ngnix  
              if ('nginx' in name and file_ext in ext_list):
                 dict_files.update({name:{'filedate':extract_date.date(),'ext':file_ext}})
              else:
                     print ('not ngnix log: '+ name)
                  
         except Exception as exc:
                       print(exc)
    #print(dict_files)
    for key, value in sorted(dict_files.items(),key=lambda x: x[1]['filedate'],reverse=True)[:1]:
          print(key,value['filedate'],value['ext'])
          return key,value['filedate'],value['ext']



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
def reader(log_dir,file_log,date_log,ext):
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    error_counter=0#счетчик ошибок
    unique_urlcnt=0#счетчик уникальных урлов
    timetotal_url=0#счетчик уникальных урлов
    time_urls={}# словарь содержит url и время
    #rx = re.compile(r'(?:GET|POST)\s+(/\S+)')
    #rx = re.compile(r'/\/(.*?)\/\?/ism')
    #file_log,date_log,ext=log_finder(log_dir)
    file_log=log_dir+'/'+file_log
    print(file_log)
    if os.path.isfile(file_log):
     try:
       with openfile(file_log,ext, 'r') as inputfile:
           lines_cnt = 0 #ограничемся пока 1000 строк
           for line in inputfile:
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
                         

                     else:
                         time_list.append(time)
                         time_urls.update({urls:
                                                 {"time_sum":time,
                                                  "time_mass":time_list,
                                                  "cnt":1}})
                         unique_urlcnt+=1

                  else:
                       print('url len=0')
                       error_counter+=1

                except Exception as exc:
                       #print(urls)
                       error_counter+=1
                       print(str(exc))
                lines_cnt+=1
                timetotal_url+=time
                if(lines_cnt==300000):
                   print(lines_cnt)
                   break

                  
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")

    else:
         #print('file not found')
         print('{0} func : file not found '.format(sys._getframe().f_code.co_name))
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

#функция возвращает топ записей из массива
def top_values(dict_stat,top_count):
#{"count": 2767, "time_avg": 62.994999999999997, "time_max": 9843.5689999999995, "time_sum": 174306.35200000001,
# "url": "/api/v2/internal/html5/phantomjs/queue/?wait=1m", "time_med": 60.073, "time_perc": 9.0429999999999993,
# "count_perc": 0.106}
    cntgot=0#количество занчений которое отдали, top_count которое требуется отдать
    list_to_render=[]
    for key, value in sorted(dict_stat.items(),key=lambda x: x[1]['time_sum'],reverse=True):
        
        print (value['time_sum'])
        list_to_render.append({"count":value['cnt'],
                               "time_avg":value['time_avg'],
                               "time_max":value['time_max'],
                               "time_sum":value['time_sum'],
                               "url":key,
                               "time_med":value['time_med'],
                               "time_perc":value['time_perc'],
                               "count_perc":value['count_perc']
                                                            })
        cntgot+=1
        if(cntgot==top_count):
            print("достатоШно")
            jsonarr = json.dumps(list_to_render)
            return jsonarr
            #print(jsonarr)
            break
        
# функция рендеринга html файла
def json_templater(json_array,report_dir,date_stamp):
    file_report=report_dir+'/report.html' #файл шаблона
    file_report_rend=report_dir+'/report-'+date_stamp.strftime("%Y.%m.%d")+'.html' #файл который рендерим, отчет
    print(file_report)
    if os.path.isfile(file_report):
       with open(file_report, 'r') as report_template:
            render_data = report_template.read()
            t = Template(render_data)
            data_export=t.safe_substitute(table_json=json_array)
       with open(file_report_rend, 'w') as output_file:
          output_file.write(data_export)

    else:
         print('file not found')

def main():
    #log_finder
    file_log,date_log,ext=log_finder(config["LOG_DIR"])
    #print(check_report(config["REPORT_DIR"],date_log))
    if(check_report(config["REPORT_DIR"],date_log)==False):
         #pass
         #reader(log_dir,file_log,date_log,ext,report_dir)
         timeurls, errcnt,uniquecnt,total_cnt,total_time=reader(config["LOG_DIR"],file_log,date_log,ext)#получаем  словарЬ со значениями и количество ошибок при парсинге
         final_dict=percent_url_counter(timeurls,uniquecnt,total_time,errcnt)
         json_mass=top_values(final_dict,10)
         json_templater(json_mass,config["REPORT_DIR"],date_log)
         print("Error count is: "+str(errcnt))
         print("unique count  is: "+str(uniquecnt))
         print("total count str  is: "+str(total_cnt))
         print("total time url   is: "+str(total_time))
    else:
         print(' уже существует. Повторный запуск не требуется')
    # топчик
    


if __name__ == "__main__":
    main()
