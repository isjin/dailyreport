#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import jira_issue
import requests
import json
from datetime import datetime
import time

jira = jira_issue.jira()

def request(jira_api_url, data=None):
    reponse = requests.get(jira_api_url, headers=headers, verify=False, data=data)
    issue_data = reponse.text
    data = json.loads(issue_data)
    return data

def link_issue(master, slave):
    data = {"type": {"name": "Relates"}, "inwardIssue": {"key": master}, "outwardIssue": {"key": slave}}
    data_json = json.dumps(data)
    return data_json


jira_issue_api = 'https://ubtjira.pvgl.sap.corp:8443/rest/api/2/issue/'
jira_myself = 'https://ubtjira.pvgl.sap.corp:8443/rest/api/2/search?jql=assignee=c5229570'
jira_issue_link_api = 'https://ubtjira.pvgl.sap.corp:8443/rest/api/2/issueLink'
headers = {
    'Content-Type': 'application/json',
    'cache-control': "no-cache",
    'authorization': 'Basic YzUyMjk1NzA6cXdlMTIzIUAj',
}
fields = {"summary": "[20170718][Morning Shift]"}


issue = jira.search_issues('issuetype=11600 and reporter=c5229570',maxResults=1)[0].fields.summary
today = datetime.now().strftime('%Y%m%d')
print today in issue