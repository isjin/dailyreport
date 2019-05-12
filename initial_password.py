#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import dailyreport_tunnel
import re


def shell_command(sql):
    shell = 'mysql -h192.168.1.3 -uroot -pInitial0  -e "%s" \n' % sql
    return shell

def initial_password():
    landscape = 'CN'
    email = 'cs47@sap.cn'
    tunnel = dailyreport_tunnel.Tunnel(landscape)
    sql_1 = "select id from CSM.USERS WHERE EMAIL = '%s';" % email
    shell_1 = shell_command(sql_1)
    data = tunnel.channel_output(shell_1)
    data = re.split(r'sapadmin', data)[1]
    user_id = re.findall(r'\d+', data)[-1:][0]
    print user_id

    # sql_2 = "SELECT password,salt FROM CSM.NAMEDUSERBINDINGS WHERE USER_ID = '%s'" % user_id
    # shell_2 = shell_command(sql_2)
    # data = tunnel.channel_output(shell_2)
    # print data

    sql_3 = "update from CSM.NAMEDUSERBINDINGS set password = (select password from CSM.NAMEDUSERBINDINGS WHERE USER_ID " \
            "='2604'),salt = (select salt from CSM.NAMEDUSERBINDINGS WHERE USER_ID ='2604') "
    shell_3 = shell_command(sql_3)
    data = tunnel.channel_output(shell_3)
    print data
    return

def del_user_eshop():
    landscape = 'CN'
    tunnel = dailyreport_tunnel.Tunnel(landscape)
    dbschema = 'ESHOPDB6968'
    user_email = '7276677308@qq.com'
    sql_1 = "Delete from %s.wp_usermeta  where user_id in (select id from %s.wp_users where user_login in ('%s'));" %(dbschema,dbschema,user_email)
    sql_2 = "Delete from %s.wp_users where user_login in ('%s')" %(dbschema,user_email)
    shell_1 = shell_command(sql_1)
    data_1 = tunnel.channel_output(shell_1)
    print data_1
    shell_2 = shell_command(sql_2)
    data_2 = tunnel.channel_output(shell_2)
    print data_2




