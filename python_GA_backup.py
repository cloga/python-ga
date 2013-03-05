# -*- coding: utf-8 -*-
import webbrowser
import urllib,urllib2,httplib2,json
proxy=httplib2.ProxyInfo(3, '127.0.0.1', 8087)
urllib2.ProxyHandler({'https':'127.0.0.1:8087'})
http = httplib2.Http(proxy_info = proxy,disable_ssl_certificate_validation=True)#指定proxy关闭SSL认证
##http = httplib2.Http()
client_id='239823730922.apps.googleusercontent.com'
client_secret='SCNzepX37mqbrwEDtmAoXnyf'
##redirect_uri='http://localhost'
redirect_uri='urn:ietf:wg:oauth:2.0:oob'
auth_server='https://accounts.google.com/o/oauth2/auth'
token_uri='https://accounts.google.com/o/oauth2/token'
scope='https://www.googleapis.com/auth/analytics.readonly'
data_uri='https://www.googleapis.com/analytics/v3/data/ga'
def get_token():
    auth_uri=auth_server+'?scope='+scope+'&state=%2Fprofile&redirect_uri='+redirect_uri+'&response_type=code&client_id='+client_id+'&approval_prompt=force&access_type=offline'
    webbrowser.open(auth_uri) 
    code=raw_input('code:')##like 4/JPxXb-9pIYgDplpl219vZsrsnosh.EkSM4OsIb8MdgrKXntQAax3otm0OegI
    body = urllib.urlencode({
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'scope': scope,
        }) 
    headers = {'content-type': 'application/x-www-form-urlencoded',}
    content = http.request(token_uri, method='POST', body=body,headers=headers)
    access_token=json.loads(content[1])['access_token']
    refresh_token=json.loads(content[1])['refresh_token']
    return access_token,refresh_token#access_token有效期为一小时，超时需使用refresh_token重新获得
    
def get_accounts(start='1', max='1000'):
  url='https://www.googleapis.com/analytics/v3/management/accounts?access_token='+access_token+'&start-index='+start+'&max-results='+max
  content=json.loads(urllib2.urlopen(url).read())
  return content

access_token,refresh_token=get_token()
profile_id='ga:36050032'
args = 'access_token='+access_token+\
       '&ids='+profile_id+\
       '&start-date='+'2013-01-01'+\
       '&end-date='+'2013-01-15'+\
       '&metrics='+'ga:visits'+\
       '&dimensions='+'ga:source,ga:keyword'+\
       '&sort='+'-ga:visits,ga:source'+\
       '&max_results='+'10000'
def get_data(args):
    content=json.loads(urllib2.urlopen(data_uri+'?'+args).read())
    return content
data=get_data(args)
headers=[i['name'] for i in data['columnHeaders']]
rows=[','.join(i).encode('gbk','ignore') for i in data['rows']]
with open('./ga_data.csv','w') as f:
    f.write(','.join(headers).encode('gbk','ignore')+'\n')
    f.write('\n'.join(rows))
print 'complete'