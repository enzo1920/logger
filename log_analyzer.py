#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import gzip
import os
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def reader():
    #проверяем наличие файла в директории
    #print(os.path.dirname(os.path.abspath(__file__)))
    file_log=os.path.dirname(os.path.abspath(__file__))+'/logs/nginx-access-ui.log-20170630.gz'
    print(file_log)
    if os.path.isfile(file_log):
     try:
       with gzip.open(file_log,'r') as gfile:
           for line in gfile:
                ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line )
                print('>>>>', line)
                print(ip)
     except KeyboardInterrupt:
               print("прерывание с клавиатуры")
     #finally:
            #file_log.close()
    else:
         print('file not found')



def main():
    #pass
    reader()

if __name__ == "__main__":
    main()
