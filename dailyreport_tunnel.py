#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import socket
import paramiko
import configparser
import time
from random import randint

cf = configparser.ConfigParser()
cf.read('config.ini')


class Tunnel(object):
    def __init__(self, landscape):
        self.proxy_server = cf.get(landscape, 'proxy_server')
        self.proxy_port = cf.get(landscape, 'proxy_port')
        self.bastion = cf.get(landscape, 'bastion')
        self.bastion_port=cf.get(landscape, 'bastion_port')
        self.bastion_user = cf.get(landscape, 'bastion_user')
        self.bastion_key = cf.get(landscape, 'bastion_key')
        self.zabbix = cf.get(landscape, 'zabbix')
        self.zabbix_key = cf.get(landscape, 'zabbix_key')
        self.landscape = landscape
        # if landscape == 'MSA':
        #     self.forward_port = int(cf.get(landscape, 'forward_port'))
        self.timesleep1 = 10
        self.timesleep2 = 2
        self.timesleep = self.timesleep2
        self.ssh = self.connect_zabbix()

    def http_proxy_tunnel_connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(600)
        sock.connect((self.proxy_server, int(self.proxy_port)))
        cmd_connect = "CONNECT %s:%d HTTP/1.1\r\n\r\n" % (self.bastion, int(self.bastion_port))
        sock.sendall(cmd_connect.encode('utf-8'))
        response = []
        sock.settimeout(10)
        try:
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response.append(chunk)
                if "\r\n\r\n".encode('utf-8') in chunk:
                    break
        except socket.error as se:
            if "timed out" not in se:
                response = [se]
        response = b''.join(response)
        if "200 connection established".encode('utf-8') not in response.lower():
            raise Exception("Unable to establish HTTP-Tunnel: %s" % repr(response))
        return sock

    #
    def connect_zabbix(self):
        while True:
            try:
                if self.landscape != 'MSA_CN':
                    sock = self.http_proxy_tunnel_connect()
                bastion = paramiko.SSHClient()
                bastion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if self.landscape != 'MSA_CN':
                    bastion.connect(hostname=self.bastion, port=443, username=self.bastion_user,
                                    key_filename=self.bastion_key,
                                    sock=sock)
                else:
                    bastion.connect(hostname=self.bastion, port=int(self.bastion_port), username=self.bastion_user,
                                    key_filename=self.bastion_key)
                transport = bastion.get_transport()
                dest_addr = (self.zabbix, 22)
                port = randint(10000, 10200)
                local_addr = ('127.0.0.1', port)
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=600)
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname='127.0.0.1', port=port, username='sapadmin', key_filename=self.zabbix_key,
                            sock=channel)
                break
            except Exception as e:
                print(self.landscape, e.__str__())
        return ssh

    def connect_server(self, dest_server):
        while True:
            try:
                if self.landscape != 'MSA_CN':
                    sock = self.http_proxy_tunnel_connect()
                bastion = paramiko.SSHClient()
                bastion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if self.landscape != 'MSA_CN':
                    bastion.connect(hostname=self.bastion, port=443, username=self.bastion_user,
                                    key_filename=self.bastion_key,
                                    sock=sock)
                else:
                    bastion.connect(hostname=self.bastion, port=int(self.bastion_port), username=self.bastion_user,
                                    key_filename=self.bastion_key)
                transport = bastion.get_transport()
                dest_addr = (dest_server, 22)
                port = randint(10000, 10200)
                local_addr = ('127.0.0.1', port)
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr, timeout=600)
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname='127.0.0.1', port=port, username='sapadmin', key_filename=self.zabbix_key,
                            sock=channel)
                break
            except Exception as e:
                print(self.landscape, e.__str__())
        return ssh

    def channel_output(self, command):
        channel = self.ssh.invoke_shell()
        channel.send(command)
        time.sleep(self.timesleep)
        output = channel.recv(9999)
        return output

    def server_channel_output(self, dest_server, command):
        server_ssh = self.connect_server(dest_server)
        channel = server_ssh.invoke_shell()
        channel.send(command)
        time.sleep(self.timesleep)
        output = channel.recv(9999)
        return output
