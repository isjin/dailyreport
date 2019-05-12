#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import configparser

cf = configparser.ConfigParser()
cf.read('config.ini')


class EsCode(object):
    def __init__(self, landscape):
        self.es_server = cf.get(landscape, 'es_server')
        self.index1 = cf.get(landscape, 'index1')
        self.index2 = cf.get(landscape, 'index2')
        self.es_http = cf.get(landscape, 'es_http')
        self.es_app = cf.get(landscape, 'es_app')
        self.es_eshop = cf.get(landscape, 'es_eshop')
        self.es_access = cf.get(landscape, 'es_access')
        self.es_occ = cf.get(landscape, 'es_occ')
        self.es_job = cf.get(landscape, 'es_job')

    def command(self, date1, date2, tp):
        if tp == 1:
            esfile = (self.es_http, self.es_app, self.es_eshop, self.es_access, self.es_occ, self.es_job)
        else:
            esfile = (self.es_access, self.es_occ, self.es_job)
        shell = []
        for i in esfile:
            with open(i) as code:
                code = code.readline()
            code = code.replace('date_timestamp1', str(date1)).replace('date_timestamp2', str(date2))
            if i in (self.es_occ, self.es_job):
                command = "curl -XPOST " + self.es_server + ":9200/" + self.index2 + "/_search -d '" + code + "'" + "\n"
            else:
                command = "curl -XPOST " + self.es_server + ":9200/" + self.index1 + "/_search -d '" + code + "'" + "\n"
            shell.append(command)
        return shell

    def analyze_command(self, esfile, index, timestamp1, timestamp2, timestamp3):
        with open(esfile) as code:
            code = code.readline()
        code_24 = code.replace('date_timestamp1', str(timestamp1)).replace('date_timestamp2', str(timestamp2))
        shell_24 = "curl -XPOST " + self.es_server + ":9200/" + index + "/_search -d '" + code_24 + "'" + "\n"
        code_48 = code.replace('date_timestamp1', str(timestamp1)).replace('date_timestamp2', str(timestamp3))
        shell_48 = "curl -XPOST " + self.es_server + ":9200/" + index + "/_search -d '" + code_48 + "'" + "\n"
        return shell_24, shell_48


class Analyze(object):
    def __init__(self, landscape):
        self.es_access_host = cf.get(landscape, 'es_access_host')
        if landscape in ('CN', 'EU'):
            self.es_job_tenant = cf.get(landscape, 'es_job_tenant')
            self.es_occ_tenant = cf.get(landscape, 'es_occ_tenant')
            self.es_access_http_agent = cf.get(landscape, 'es_access_http_agent')
        elif landscape == 'MSA':
            self.es_access_http_agent = cf.get(landscape, 'es_access_http_agent')
            self.es_common = cf.get(landscape, 'es_common')
            self.es_common_level = cf.get(landscape, 'es_common_level')
            self.es_service = cf.get(landscape, 'es_service')
        else:
            pass
