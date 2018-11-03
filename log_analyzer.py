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
import logging
import ConfigParser
import argparse
#import gc
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';



config = {
    "REPORT_SIZE": 20,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "MAX_ERR": 30,
    "WORK_LOG":"./work_log"
}
config_file_global="./log_analyzer.cfg"


#считыватель конфига
def config_reader(config_default,fileconf_input):
    if(fileconf_input.configname is not None):
        config_file=fileconf_input.configname
    else:
        config_file=config_file_global
    if os.path.isfile(config_file):
       logging.info("config found")
       config = ConfigParser.RawConfigParser()
       config.read(config_file)
       for section_name in config.sections():
           #print 'Section:', section_name
           #print '  Options:', config.options(section_name)
           if(len(config.items(section_name))!=0):
                    for name, value in config.items(section_name):
                        name=name.upper()

                        if(name in config_default):
                           config_default.update({name:value})
                        else:
                             logging.info(name+ 'not fount in difault config')
           else:
                  logging.info('Input config is empty. I will use default config ')
    else:
       logging.info("config file not found. I will use default config")
    return config_default

#настройка лога
def worker_log(worklog_dir):
    if not os.path.exists(worklog_dir):
         os.makedirs(worklog_dir)
    worklog_file=worklog_dir+'/work_log-'+datetime.datetime.now().strftime("%Y.%m.%d_%H-%M-%S")+'.log'
    open(worklog_file, 'a').close()
    print(worklog_file)
    logging.basicConfig(level=logging.DEBUG,format='[%(asctime)s] %(levelname).1s %(message)s',datefmt='%Y.%m.%d %H:%M:%S',filename=worklog_file, filemode='w')
    logging.info("worker_log is set")

#декоратор время выполнения
def benchmark(original_func):
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = original_func(*args, **kwargs)
        end = datetime.datetime.now()
        print('{0} is executed in {1}'.format(original_func.__name__, end-start))
        #print('{0} is executed in {1}'.format(original_func.__name__, end-start))
        return result
    return wrapper

#функция проверки существования файла отчета
def check_report(report_dir,date_stamp):
    file_report_rend=report_dir+'/report-'+date_stamp.strftime("%Y.%m.%d")+'.html' #файл который рендерим, отчет
    
    if os.path.exists(file_report_rend):
         logging.info('File is alive  '+file_report_rend)
         return True 
    else:
         logging.info('{0} func : file not found {1}'.format(sys._getframe().f_code.co_name,file_report_rend))
         #print('File not found  '+file_report_rend)
         return False 


#функция открытия файла gzip или plain
def openfile(filename,file_ext, mode='r'):
    if (file_ext=='gz'):
        return gzip.open(filename, mode) 
    else:
        return open(filename, mode)

#функция поиска самого свежего лога
def log_finder(log_dir):
    files = os.listdir(log_dir)
    dict_files={}
    extract_err=0
    #какие расширения файла будем открывать
    ext_list=['gz','plain']
    for name in files:
         split_names=name.split('.')
         extract_err=0


         try:
            extract_date=datetime.datetime.strptime(split_names[1][4:], '%Y%m%d')
         except Exception as exc:
                       logging.warning(exc)
                       extract_err=1
         if(extract_err==0):
            year=extract_date.year
            month='{:02d}'.format(extract_date.month)
            day='{:02d}'.format(extract_date.day)
            str_date=str(year)+'.'+str(month)+'.'+str(day)
            if(len(split_names)>2):
                  logging.info(split_names[0]+' has date: '+str_date+' ext is:'+split_names[2])
                  file_ext=split_names[2]
            else:
                  logging.info(split_names[0]+' has date: '+str_date+' ext not found. plain ')
                  file_ext='plain'
              #в словарь пойдут только логи ngnix  
            if ('nginx' in name and file_ext in ext_list):
                 dict_files.update({name:{'filedate':extract_date.date(),'ext':file_ext}})
            else:
                     logging.info('not ngnix log: '+ name)
                  

    #print(len(dict_files))
    #проверка , что в словаре что-то есть. А вдруг нет ничего!
    if(len(dict_files)>0):
        for key, value in sorted(dict_files.items(),key=lambda x: x[1]['filedate'],reverse=True)[:1]:
            #print(key,value['filedate'],value['ext'])
            return key,value['filedate'],value['ext']
    else:
          return None,None,None



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
def reader(log_dir,file_log,date_log,ext,max_err):
    #проверяем наличие файла в директории
    logging.info("reader start")
    error_counter=0#счетчик ошибок
    unique_urlcnt=0#счетчик уникальных урлов
    timetotal_url=0#счетчик уникальных урлов
    time_urls={}# словарь содержит url и время
    file_log=log_dir+'/'+file_log
    print(file_log)
    if os.path.isfile(file_log):
       with openfile(file_log,ext, 'r') as inputfile:
           lines_cnt = 0 #ограничемся пока 1000 строк
           for line in inputfile:
                finded =line.split(' ')
                #считаем согласно формату, что урл 7, если он не 7 значит формат менялся, очевидно нужно добавить регулярку , чтобы заматчить
                urls =finded[7].strip() 
                time=float(line[-6:])
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
                       logging.info('url len=0')
                       error_counter+=1

                except Exception as exc:
                       error_counter+=1
                       logging.exception(exc)
                lines_cnt+=1
                timetotal_url+=time



    else:
         logging.warning('{0} func : file not found '.format(sys._getframe().f_code.co_name))
         time_urls={}
         error_counter=max_err
         unique_urlcnt=0,
         lines_cnt=0
         timetotal_url=0
    return time_urls,error_counter,unique_urlcnt,lines_cnt,timetotal_url


#функция для подсчета процентов на вход словарь с урлами и временем, на выходе словарь урл, время, процент процентами 
@benchmark
def percent_url_counter(dict,uniq_url,time_sum,err):
#считаем статистику для урла
    dict_percent=dict
    logging.info("percent_url_counter start")
    for k,v in dict.iteritems():
           dict_percent[k]["count_perc"]=100*float(dict[k]["cnt"])/float(uniq_url)
           dict_percent[k]["time_perc"]=100*dict[k]["time_sum"]/float(time_sum)
           dict_percent[k]["time_avg"]=dict[k]["time_sum"]/dict[k]["cnt"]
           list_to_max=dict_percent[k]["time_mass"]
           #максимум времени
           dict_percent[k]["time_max"]=max(list_to_max)
           #медиана времени
           dict_percent[k]["time_med"]=median(list_to_max)

    return dict

#функция возвращает топ записей из массива
def top_values(dict_stat,top_count):
    logging.info("top_values start")
    cntgot=0#количество занчений которое отдали, top_count которое требуется отдать
    list_to_render=[]
    for key, value in sorted(dict_stat.items(),key=lambda x: x[1]['time_sum'],reverse=True):
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
            logging.info("top_values: получено запрошенное количество значений . Топчик")
            jsonarr = json.dumps(list_to_render)
            break
        else:
          jsonarr = json.dumps(list_to_render[cntgot-1])
    return jsonarr

# функция рендеринга html файла
def json_templater(json_array,report_dir,date_stamp):
    file_report=report_dir+'/report.html' #файл шаблона
    file_report_rend=report_dir+'/report-'+date_stamp.strftime("%Y.%m.%d")+'.html' #файл который рендерим, отчет
    logging.warning(file_report)
    if os.path.isfile(file_report):
       with open(file_report, 'r') as report_template:
            render_data = report_template.read()
            t = Template(render_data)
            data_export=t.safe_substitute(table_json=json_array)
#здесь нужно писать во временный файл, потом делать мув
       with open(file_report_rend, 'w') as output_file:
          output_file.write(data_export)

    else:
         loggin.warning('json_templater file not found') #добавить  обработку, если файл шаблона не найден

def main(*args):

    dict_config=config_reader(args[0],args[1])
    report_sz=int(dict_config["REPORT_SIZE"])
    worker_log(dict_config["WORK_LOG"])
    file_log,date_log,ext=log_finder(dict_config["LOG_DIR"])
    if(file_log is None):
        logging.info(" main: no log files")
    else:
         if(check_report(dict_config["REPORT_DIR"],date_log)==False):
              #получаем  словарЬ со значениями и количество ошибок при парсинге
              timeurls, errcnt,uniquecnt,total_cnt,total_time=reader(dict_config["LOG_DIR"],file_log,date_log,ext,dict_config["MAX_ERR"])
              #доля ошибок парсинга
              parse_err=errcnt*100/total_cnt
              if(parse_err<=dict_config["MAX_ERR"]):
                   final_dict=percent_url_counter(timeurls,uniquecnt,total_time,errcnt)
                   json_mass=top_values(final_dict,report_sz)
                   json_templater(json_mass,dict_config["REPORT_DIR"],date_log)
                   print("Error count is: "+str(errcnt))
                   print("unique count  is: "+str(uniquecnt))
                   print("total count str  is: "+str(total_cnt))
                   print("total time url   is: "+str(total_time))
              else:
                    logging.exception('Log parse errors is '+dict_config["MAX_ERR"]+'%. Exit program!!!!!')
                    sys.exit()
         else:
              logging.info(" REPORT уже существует. Повторный запуск не требуется")

    


if __name__ == "__main__":
 
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',dest="configname",required=False)
    args = parser.parse_args()
    main(config,args)
