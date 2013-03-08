# -*- coding: utf-8 -*-
##需增加token持久化及刷新的机制
##需增加出现抽样后，将粒度变小的逻辑
import webbrowser,os
import collections
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
    
def get_data(args):
    url=data_uri+'?'+args
    print '解析数据,打开:\n'+url
    content=json.loads(urllib2.urlopen(url).read())
    headers=[i['name'] for i in content['columnHeaders']]
    rows=[','.join(i).encode('gbk','ignore') for i in content['rows']]
    if content['totalResults']<=10000:
        return headers,rows
    elif content['totalResults']>10000:
        for i in range(2,content['totalResults']/10000+1):
            url0=url+'&start-index='+str(i*10000)
            print '解析数据,打开:\n'+url0
            content0=json.loads(urllib2.urlopen(url0).read())
            rows+=[','.join(i).encode('gbk','ignore') for i in content0['rows']]
        return headers,rows
def get_mcf_data(args):
    url=mcf_uri+'?'+args
    print '解析数据,打开:\n'+url
    content=json.loads(urllib2.urlopen(url).read())
    headers=[i['name'] for i in content['columnHeaders']]
    rows= content['rows']
    if content['totalResults']<=10000:
        return headers,rows
    else:
        for i in range(2,content['totalResults']/10000+1):
            url0=url+'&start-index='+str(i*10000)
            print '解析数据,打开:\n'+url0
            content0=json.loads(urllib2.urlopen(url0).read())
            print len(rows)
            rows+= content0['rows']
        return headers,rows

def write_data(headers,rows,name='ga_data'):
    content=','.join(headers).encode('gbk','ignore')+'\n'+'\n'.join(rows)
    with open('./'+name+'.csv','w') as f:
        f.write(content)
    print "Data has been writen!"
def agg_dic(dic,key,value):##给定channel名，算channel的值
    if dic.has_key(key):
        dic[key]=[float(dic[key][0])+float(value[0]),float(dic[key][1])+float(value[1])]##已有channel
    else:
        dic[key]=value##新channel
def output_dic(file,dic):
    for k in dic.keys():
##        print k,dic[k][0],dic[k][1]
        file.write('%s,%s,%s\n' % (k,dic[k][0],dic[k][1]))
    file.write('\n\n\n')
def write_funnel_data(headers,rows,name='funnel_data'):
    funnels_list=[]
    for i in rows:
        funnels_list+=[str(j['nodeValue']) for j in i[0]['conversionPathValue']]
    covs=[str(i[1]['primitiveValue']) for i in rows]
    vals=[str(i[2]['primitiveValue']) for i in rows]
    lines=[funnels_list[n]+','+covs[n]+','+vals[n] for n in range(len(funnels_list))]
    content=','.join(headers).encode('gbk','ignore')+'\n'+'\n'.join(lines)
    with open('./'+name+'.csv','w') as f:
        f.write(content)
    print "Funnel Data has been writen!"
def write_mcf_data(headers,rows,name='mcf_data'):
    dic_f={}##first touch
    dic_l={}##last touch
    dic_ln={}##linear
    funnels_list=[]
    for i in rows:
        paths=[str(j['nodeValue']) for j in i[0]['conversionPathValue']]
        covs=i[1]['primitiveValue']
        vals=i[2]['primitiveValue']
        if len(paths)==1:
            channel=paths
            cov=[covs,vals]
            agg_dic(dic_f,channel[0],cov)
            agg_dic(dic_l,channel[0],cov)
            agg_dic(dic_ln,channel[0],cov)
        else:
            ##first touch
            channel=paths[0]
            cov=[covs,vals]
            agg_dic(dic_f,channel,cov)
            ##last touch
            channel=paths[-1]
            agg_dic(dic_l,channel,cov)
            ##linear
            channels_list=collections.Counter(paths).most_common()
            for c in channels_list:
                weight=c[1]/len(paths)
                cov=[float(covs)*weight,float(vals)*weight]
                agg_dic(dic_ln,c[0],cov)
    with open (name+'.csv','w') as f:
        f.write('-----first touch------\n')
        f.write('channel,conversions,value\n')
        output_dic(f,dic_f)
        f.write('-----last touch------\n')
        f.write('channel,conversions,value\n')
        output_dic(f,dic_l)
        f.write('-----linear------\n')
        f.write('channel,conversions,value\n')
        output_dic(f,dic_ln)
        print "MCF Data has been writen!"

access_token,refresh_token=get_token()
profile_id='ga:XXXX'##要查询数据的Profile_id
args = 'access_token='+str(access_token)+\
       '&ids='+profile_id+\
       '&start-date='+'2012-09-03'+\
       '&end-date='+'2013-01-15'+\
       '&metrics='+'mcf:totalConversions,mcf:totalConversionValue'+\
       '&dimensions='+'mcf:basicChannelGroupingPath'+\
       '&max-results='+'10000'
headers,rows=get_mcf_data(args)
write_mcf_data(headers,rows)
print 'complete'