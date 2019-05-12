#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
from datetime import datetime, timedelta
import dailyreport_tunnel
import dailyreport_escode
import re
import json
import configparser


def timestamp(time_stamp):
    time_tup = time_stamp.timetuple()
    time_stamp = time.mktime(time_tup) * 1000 + now.microsecond / 1000
    return int(time_stamp)


now = datetime.now()
yesterday = now - timedelta(days=1)
twodaysago = now - timedelta(days=2)
fivemago = now - timedelta(minutes=5)
date_timestamp1 = timestamp(now)
date_timestamp2 = timestamp(yesterday)
date_timestamp3 = timestamp(twodaysago)
date_timestamp4 = timestamp(fivemago)
# print(date_timestamp1,date_timestamp4)

cf = configparser.ConfigParser()
cf.read('config.ini')


class Data(object):
    def __init__(self, landscape):
        self.tunnel = dailyreport_tunnel.Tunnel(landscape)
        self.escode = dailyreport_escode.EsCode(landscape)
        self.landscape = landscape
        self.hana_server1 = cf.get(landscape, 'hana_server1')
        self.hana_server2 = cf.get(landscape, 'hana_server2')

    # hana expire
    def hana(self):
        shell = 'bash /home/sapadmin/HANA_check.sh' + '\n'
        output = self.tunnel.channel_output(shell)
        hana_status = []
        data = re.sub(r'\[|\]|\'|\\r|\\n|\s', '', str(output))
        data = data.split('sapadmin@')[1].replace(' ', '').split(',')
        data = re.findall(r'(OK:\w+|WARNING:\w+)', str(data))

        day = re.findall(r'\d+', data[0])
        hana_status.append(day[0])
        for i in (1, 2):
            status = re.search(r'successful', data[i])
            status = ('failed' if status is None else 'successful')
            hana_status.append(status)
        return hana_status

    # check_s3_backup
    def s3_backup(self):
        shell = 'more /tmp/s3backup.log \n'
        output = self.tunnel.channel_output(shell).decode('utf-8')
        status = re.findall(r'successful|failed|error', output)
        status_cn = [status[0], status[1], status[2]]
        status_msa = [status[3], status[4], status[5]]
        # status_msa = [status[6], status[7], status[8]]
        # status_msa = [status[9], status[10], status[11]]
        s3_status = [status_cn, status_msa]
        return s3_status

    # esdata
    def esdata(self, shell):
        if self.landscape == 'US' or self.landscape == 'EU':
            del self.tunnel
            while True:
                try:
                    self.tunnel = dailyreport_tunnel.Tunnel('MSA')
                    break
                except Exception as e:
                    print(self.landscape, e.__str__())
        while True:
            try:
                output = self.tunnel.channel_output(shell)
                data = str(output).split('sapadmin@')[1]
                data = str(data).split(r'\n')[1]
                data = json.loads(data)
                if 'hits' in data:
                    self.tunnel.timesleep = self.tunnel.timesleep2
                    break
            except Exception as e:
                print(self.landscape, e.__str__())
                self.tunnel.timesleep = self.tunnel.timesleep1
        return data

    # http
    def http(self):
        shell = self.escode.command(date_timestamp1, date_timestamp2, 1)[0]
        data = self.esdata(shell)
        return data

    # pv
    def pv(self):
        count = []
        for i in range(0, 2):
            shell = self.escode.command(date_timestamp1, date_timestamp2, 1)[1 + i]
            data = self.esdata(shell)["hits"]['total']
            count.append(str(data))
        return count

    # log
    def log(self, number):
        count = []
        key1 = "hits"
        key2 = 'total'
        for j in range(3, 6 - number):
            log_escode_24 = self.escode.command(date_timestamp1, date_timestamp2, 1)[j]
            log_count_24 = self.esdata(log_escode_24)[key1][key2]
            count.append(str(log_count_24))
        for k in range(0, 3 - number):
            log_escode_48 = self.escode.command(date_timestamp1, date_timestamp3, 2)[k]
            log_count_48 = self.esdata(log_escode_48)[key1][key2]
            count.append(str(log_count_48))
        return count

    def analyze_data(self, esfile, index):
        key1 = 'aggregations'
        key3 = 'buckets'

        shell_24, shell_48 = self.escode.analyze_command(esfile, index, date_timestamp1, date_timestamp2,
                                                         date_timestamp3)
        # print(esfile,shell_24)
        if esfile == './escode/msa/access_http_agent.txt' or esfile == './escode/msa/access_host.txt':
            key2 = '3'
        else:
            key2 = '2'
        data_24 = self.esdata(shell_24)[key1][key2][key3]
        data_48 = self.esdata(shell_48)[key1][key2][key3]
        # print(data_24)
        return data_24, data_48

    def analyze(self, esfile, index, line, area):
        dict_analyze = {}
        domains = []
        data_24, data_48 = self.analyze_data(esfile, index)
        for y in range(0, len(data_24)):
            domain = data_24[y]['key']
            count_24 = data_24[y]['doc_count']
            domain_row = area[0] + str(line + y)
            count24_row = area[1] + str(line + y)
            dict_analyze[domain_row] = domain
            dict_analyze[count24_row] = count_24
            domains.append(domain)
        dict_data48 = {}
        for z in range(0, len(data_48)):
            domain = data_48[z]['key']
            count_48 = data_48[z]['doc_count']
            dict_data48[domain] = count_48
        for u in range(0, len(data_24)):
            count48 = area[2] + str(line + u)
            check_key = domains[u] in dict_data48.keys()
            if check_key is True:
                dict_analyze[count48] = dict_data48[domains[u]]
            else:
                dict_analyze[count48] = ''
        return dict_analyze

    @staticmethod
    def service(service_data):
        service_total_info = []
        for p in range(0, len(service_data)):
            service_info = []
            service_name = service_data[p]['key']
            level = service_data[p]['3']['buckets']
            for i in (service_name, level):
                service_info.append(i)
            service_total_info.append(service_info)
        return service_total_info

    def service_analyze(self, esfile, index, line, area):
        shell_24, shell_48 = self.escode.analyze_command(esfile, index, date_timestamp1, date_timestamp2,
                                                         date_timestamp3)
        service_data_24 = self.esdata(shell_24)['aggregations']['2']['buckets']
        service_data_48 = self.esdata(shell_48)['aggregations']['2']['buckets']
        service_24 = self.service(service_data_24)
        service_48 = self.service(service_data_48)
        data_48_dict = dict(service_48)
        data_new = []
        for i in range(0, len(service_24)):
            data = service_24[i]
            if data[0] in data_48_dict.keys():
                data = data + [data_48_dict[data[0]]]
                data_new.append(data)
        s_dict = {}
        for j in range(0, len(data_new)):
            s_name = data_new[j][0]
            for k in range(0, len(data_new[j][1])):
                s_name_row = area[0] + str(line + 3 * j + k)
                s_level_row = area[1] + str(line + 3 * j + k)
                s_24_row = area[2] + str(line + 3 * j + k)
                s_dict[s_name_row] = s_name
                s_dict[s_level_row] = data_new[j][1][k]['key']
                s_dict[s_24_row] = data_new[j][1][k]['doc_count']
            for l in range(0, len(data_new[j][2])):
                s_name_row = area[0] + str(line + 3 * j + l)
                s_level_row = area[1] + str(line + 3 * j + l)
                s_48_row = area[3] + str(line + 3 * j + l)
                s_dict[s_name_row] = s_name
                s_dict[s_level_row] = data_new[j][2][l]['key']
                s_dict[s_48_row] = data_new[j][2][l]['doc_count']
        return s_dict

    def check_es_index(self, number):
        count = []
        key1 = "hits"
        key2 = 'total'
        for j in range(3, 6 - number):
            log_escode_five = self.escode.command(date_timestamp1, date_timestamp4, 1)[j]
            log_count_five = self.esdata(log_escode_five)[key1][key2]
            count.append(str(log_count_five))
        return count

    def hana_disk_check(self, row_space):
        server1_disk_check = []
        server2_disk_check = []
        disk_status = {}
        disk_check = {self.hana_server1: server1_disk_check, self.hana_server2: server2_disk_check}
        cmd = "df -h \n"
        for i in (self.hana_server1, self.hana_server2):
            output = self.tunnel.server_channel_output(i, cmd)
            df_info = str(output).split('df -h')[1].split('sapadmin')[0].split(r'\r\n')[2:-1]
            if len(df_info) ==0:
                df_info = str(output).split('df -h')[2].split('sapadmin')[0].split(r'\r\n')[2:-1]
            for line in df_info:
                disk_info = []
                data = re.split(r'\s', line)
                filename = data[-1]
                usage = data[-2]
                if 'iso' not in filename:
                    disk_info.append(filename)
                    disk_info.append(usage)
                    disk_check[i].append(tuple(disk_info))
        server1_disk_check = list(set(server1_disk_check))
        server2_disk_check = list(set(server2_disk_check))
        server1_disk_check.sort()
        server2_disk_check.sort()
        z = 0
        for x in (server1_disk_check, server2_disk_check):
            for j in range(0, len(x)):
                for k in range(len(x[j])):
                    row = row_space[z][k] + str(55 + j)
                    disk_status[row] = x[j][k]
            z += 1
        return disk_status
