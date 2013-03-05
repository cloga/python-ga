# -*- coding: utf-8 -*-
##需增加token持久化及刷新的机制
##需增加超过1W条循环提取的逻辑
##需增加出现抽样后，将粒度变小的逻辑
import webbrowser
import urllib,urllib2,httplib2,json
proxy=httplib2.ProxyInfo(3, '127.0.0.1', 8087)
##定义urllib2的proxy
proxy0=urllib2.ProxyHandler({'https':'127.0.0.1:8087'})
opener=urllib2.build_opener(proxy0)
urllib2.install_opener(opener)
http = httplib2.Http(proxy_info = proxy,disable_ssl_certificate_validation=True)#指定proxy关闭SSL认证
##http = httplib2.Http()
client_id='239823730922.apps.googleusercontent.com'#请替换为你的Client_id
client_secret='SCNzepX37mqbrwEDtmAoXnyf'#请替换为你的Client_secret
redirect_uri='urn:ietf:wg:oauth:2.0:oob'
auth_server='https://accounts.google.com/o/oauth2/auth'
token_uri='https://accounts.google.com/o/oauth2/token'
scope='https://www.googleapis.com/auth/analytics.readonly'
data_uri='https://www.googleapis.com/analytics/v3/data/ga'
mcf_uri='https://www.googleapis.com/analytics/v3/data/mcf'
def get_token():
    auth_uri=auth_server+'?scope='+scope+'&state=%2Fprofile&redirect_uri='+redirect_uri+'&response_type=code&client_id='+client_id+'&approval_prompt=force&access_type=offline'
    webbrowser.open(auth_uri)
    print '进行认证,浏览器打开:\n'+auth_uri
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
    return access_token,refresh_token##access_token有效期为一小时，超时需使用refresh_token重新获得
    
access_token,refresh_token=get_token()
profile_id='ga:63228014'##要查询数据的Profile_id
args = 'access_token='+str(access_token)+\
       '&ids='+profile_id+\
       '&start-date='+'2012-09-03'+\
       '&end-date='+'2013-01-15'+\
       '&metrics='+'mcf:totalConversions,mcf:totalConversionValue'+\
       '&dimensions='+'mcf:sourceMediumPath'+\
       '&max_results='+'10000'
def get_data(args,type='ga'):
    '''type指定获取的数据类型，普通数据为ga，mcf数据为mcf'''
    if type=='mcf':
        url=mcf_uri+'?'+args
    elif type=='ga':
        url=data_uri+'?'+args
    print '解析数据,打开:\n'+url
    content=json.loads(urllib2.urlopen(url).read())
    return content
def write_csv(data,type='ga'):
    '''type指定写入的数据格式，普通数据为ga，funnel数据为funnel，mcf数据为mcf'''
    if type=='ga':
        headers=[i['name'] for i in data['columnHeaders']]
        rows=[','.join(i).encode('gbk','ignore') for i in data['rows']]
        content=','.join(headers).encode('gbk','ignore')+'\n'+'\n'.join(rows)
    elif type=='funnel':        
        headers=[i['name'] for i in data['columnHeaders']]
        funnels_list=[]
        rows=data['rows']
        for i in rows:
            funnels_list+=[' -> '.join([str(j['nodeValue']) for j in i[0]['conversionPathValue']])]
        covs=[str(i[1]['primitiveValue']) for i in rows]
        vals=[str(i[2]['primitiveValue']) for i in rows]
        lines=[funnels_list[n]+','+covs[n]+','+vals[n] for n in range(len(funnels_list))]
        content=','.join(headers).encode('gbk','ignore')+'\n'+'\n'.join(lines)
    elif type=='mcf':
        pass
    with open('./ga_data.csv','w') as f:
        f.write(content)
    print "Data has been writen!"
mcf_data=get_data(args,type='mcf')
print 'complete'
write_csv(mcf_data,type='funnel')