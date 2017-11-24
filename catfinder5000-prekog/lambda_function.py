from urllib2 import urlopen as wget
import datetime
import os
from pprint import pprint
import json
from decimal import Decimal
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr
import urlparse
import hashlib
import urllib2
import xml.etree.ElementTree as ET
from botocore.exceptions import ClientError
import uuid


## These are unique and must be set
# S3_BUCKET = "not-set"
DELTA_URL = 'not-set'
DELTA_CONTENTNAME = 'not-set'


## hardcoded for console use
DYNAMO_MAIN = "catfinder5000-main"
DYNAMO_MAIN_GSI = "id_type-id_filename-index"
DYNAMO_LIST = "catfinder5000-list"
DYNAMO_SUMMARY = "catfinder5000-summary"

## Elemental REST API Keys
apikey = "xxxxxxx"
user = "xxxxxx"


dynamodb = boto3.resource('dynamodb')


def get_environment_variables():
    # global S3_BUCKET 
    global DELTA_URL 
    global DELTA_CONTENTNAME 
    global DYNAMO_MAIN 
    global DYNAMO_MAIN_GSI 
    global DYNAMO_LIST 
    global DYNAMO_SUMMARY 

    # if os.environ.get('S3_BUCKET') is not None:
    #     S3_BUCKET = os.environ['S3_BUCKET']
    #     print('environment variable S3_BUCKET was found: {}'.format(S3_BUCKET))
    if os.environ.get('DYNAMO_MAIN') is not None:
        DYNAMO_MAIN = os.environ['DYNAMO_MAIN']
        print('environment variable DYNAMO_MAIN was found: {}'.format(DYNAMO_MAIN))
    if os.environ.get('DYNAMO_MAIN_GSI') is not None:
        DYNAMO_MAIN_GSI = os.environ['DYNAMO_MAIN_GSI']
        print('environment variable DYNAMO_MAIN_GSI was found: {}'.format(DYNAMO_MAIN_GSI))
    if os.environ.get('DYNAMO_LIST') is not None:
        DYNAMO_LIST = os.environ['DYNAMO_LIST']
        print('environment variable DYNAMO_LIST was found: {}'.format(DYNAMO_LIST))
    if os.environ.get('DYNAMO_SUMMARY') is not None:
        DYNAMO_SUMMARY = os.environ['DYNAMO_SUMMARY']
        print('environment variable DYNAMO_SUMMARY was found: {}'.format(DYNAMO_SUMMARY))
    if os.environ.get('DELTA_URL') is not None:
        DELTA_URL = os.environ['DELTA_URL']
        print('environment variable DELTA_URL was found: {}'.format(DELTA_URL))
    if os.environ.get('DELTA_CONTENTNAME') is not None:
        DELTA_CONTENTNAME = os.environ['DELTA_CONTENTNAME']
        print('environment variable DELTA_CONTENTNAME was found: {}'.format(DELTA_CONTENTNAME))


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def elemental_api(my_urlinput, methods='GET', payload='', datatype='xml'):
    
    datatype_str = 'application/xml'
    if datatype == 'xml':
        datatype_str = 'application/xml'
    if datatype == 'json':
        datatype_str = 'application/json'
    futuretime2 = 2
    currenttime = time.time()
    finaltime = int(currenttime + futuretime2 * 60)
    parsed = urlparse.urlparse(my_urlinput)
    url = parsed.path
    print(url, datatype_str, methods, datatype)
    ###creating the REST API hash information
    prehash = "%s%s%s%s" % (url,user,apikey,finaltime)
    mdinner = hashlib.md5(prehash).hexdigest()
    prehash2 = "%s%s" % (apikey,mdinner)
    finalhash =  hashlib.md5( prehash2 ).hexdigest()
    req = urllib2.Request(my_urlinput)
    req.add_header("Content-type", datatype_str)
    req.add_header("Accept", datatype_str)
    req.add_header("X-Auth-User", user)
    req.add_header("X-Auth-Expires", finaltime)
    req.add_header("X-Auth-Key", finalhash)
    if methods == "POST":
        req.get_method = lambda: 'POST'
    if methods == "GET":
        req.get_method = lambda: 'GET'
    if methods == "PUT":
        req.get_method = lambda: 'PUT'
    if methods == "DELETE":
        req.get_method = lambda: 'DELETE'
    response_xml = urllib2.urlopen(url=req, data=payload).read()
    return(response_xml)        

def delta_contents(url):
    content_list = list()
    this_url = url + 'api/contents'
    callback_str = elemental_api(this_url)
    doc = ET.fromstring(callback_str)
    for content in doc.findall('content'):
        this_content = dict()
        this_content['id'] = content.find('id').text
        this_content['name'] = content.find('name').text
        this_content['type'] = content.find('type').text
        this_content['status'] = content.find('status').text
        this_content['vod'] = content.find('vod').text
        content_list.append(this_content)
    return(content_list)

def delta_frameaccurateput(url, content_id, query_dict):
    urlinput = url + 'contents/' + str(content_id)
    description_master = query_dict['label'] + ';'+ str(uuid.uuid4())
    data = '''<?xml version="1.0" encoding="UTF-8"?>
<content href="/contents/1" product="Delta" version="2.1.2.200205">
  <filters>
    <filter>
      <label>Filter 10</label>
      <filter_type>mp4_package</filter_type>
      <endpoint>true</endpoint>
      <url_extension>mp4</url_extension>
      <output_url nil="true"/>
      <description > <![CDATA[ ''' + description_master +''' ]]> </description>
      <use_default_stream_sets>true</use_default_stream_sets>
      <name>filter_10</name>
      <parent_filter>filter_8</parent_filter>
      <filter_settings>
        <major_brand nil="true"/>
        <include_cslg>false</include_cslg>
      </filter_settings>
    </filter>  
    <filter>
      <label>Filter 9</label>
      <filter_type>hls_package</filter_type>
      <endpoint>true</endpoint>
      <url_extension>m3u8</url_extension>
      <output_url nil="true"/>
      <description > <![CDATA[ ''' + description_master +''' ]]> </description>
      <use_default_stream_sets>true</use_default_stream_sets>
      <name>filter_9</name>
      <parent_filter>filter_8</parent_filter>
      <filter_settings>
        <segment_duration>9</segment_duration>
        <index_duration>60</index_duration>
        <playlist_type>NONE</playlist_type>
        <avail_trigger>all</avail_trigger>
        <ad_markers>none</ad_markers>
        <broadcast_time>false</broadcast_time>
        <ignore_web_delivery_allowed>false</ignore_web_delivery_allowed>
        <ignore_no_regional_blackout>false</ignore_no_regional_blackout>
        <enable_blackout>false</enable_blackout>
        <enable_network_end_blackout>false</enable_network_end_blackout>
        <network_id nil="true"/>
        <include_program_date_time>false</include_program_date_time>
        <program_date_time_interval>600</program_date_time_interval>
      </filter_settings>
    </filter>
    <filter>
      <label>Filter 8</label>
      <filter_type>live_to_vod</filter_type>
      <endpoint>false</endpoint>
      <url_extension>m3u8</url_extension>
      <output_url nil="true"/>
      <description > <![CDATA[ ''' + description_master +''' ]]> </description>
      <name>filter_8</name>
      <parent_filter></parent_filter>
      <filter_settings>
        <start_time>''' + query_dict['time_start'] + '''</start_time>
        <end_time>''' + query_dict['time_end'] + '''</end_time>
        <start_over>true</start_over>
        <allow_url_start_end_params>false</allow_url_start_end_params>
        <start_frame>''' + str(query_dict['time_start_frame']) + '''</start_frame>
        <end_frame>''' + str(query_dict['time_end_frame']) + '''</end_frame>
        <frame_accurate>true</frame_accurate>
        <lowest_framerate_numerator>30</lowest_framerate_numerator>
        <lowest_framerate_denominator>1</lowest_framerate_denominator>
      </filter_settings>
    </filter>
  </filters>
</content>'''
    # print(data)
    callback_str = elemental_api(urlinput, "PUT", data)
    doc = ET.fromstring(callback_str)
    # print doc
    delta_filters = {}
    live_endpoint = ''
    mp4_endpoint = ''
    hls_endpoint = ''
    livetovod_id = ''
    for this_filter in doc.findall('.//filter'):
        filter_id = this_filter.find('id').text
        filter_type = this_filter.find('filter_type').text
        # print(this_filter, this_filter, filter_type)

        if this_filter.find('description').text != None:
            if this_filter.find('description').text.strip() == description_master:
                delta_filters[filter_id] = {}
                delta_filters[filter_id]['id'] = filter_id
                delta_filters[filter_id]['type'] = this_filter.find('filter_type').text
                if this_filter.find('filter_type').text == 'mp4_package':
                    delta_filters[filter_id]['endpoint'] =  this_filter.find('default_endpoint_uri').text
                    mp4_endpoint = this_filter.find('default_endpoint_uri').text
                if this_filter.find('filter_type').text == 'hls_package':
                    delta_filters[filter_id]['endpoint'] = this_filter.find('default_endpoint_uri').text
                    hls_endpoint = this_filter.find('default_endpoint_uri').text
                if this_filter.find('filter_type').text == 'live_to_vod':
                    delta_filters[filter_id]['start_time'] = this_filter.find('filter_settings/start_time').text  
                    delta_filters[filter_id]['start_frame'] = this_filter.find('filter_settings/start_frame').text
                    delta_filters[filter_id]['end_time'] = this_filter.find('filter_settings/end_time').text 
                    delta_filters[filter_id]['end_frame'] = this_filter.find('filter_settings/end_frame').text
                    livetovod_id = filter_id
    put_dynamo(livetovod_id, mp4_endpoint, hls_endpoint, delta_filters, query_dict)
    # get_videofile(mp4_endpoint, livetovod_id)
    return delta_filters

def put_dynamo(livetovod_id, mp4_endpoint, hls_endpoint, delta_filters, query_dict):
    print("put_dynamo to table: " + str(DYNAMO_LIST))
    table = dynamodb.Table(DYNAMO_LIST)
    this_uuid = str(uuid.uuid4())
    try:
        response = table.put_item(
            Item={
                    'entry_id': this_uuid,
                    'timestamp_created': int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds()),
                    'timestamp_ttl': int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds() + 900 ),
                    'label': query_dict['label'],
                    'time_start': query_dict['time_start'],
                    'time_start_frame': query_dict['time_start_frame'],
                    'time_start_image': query_dict['time_start_image'],
                    'time_end': query_dict['time_end'],
                    'time_end_frame': query_dict['time_end_frame'],
                    'time_end_image': query_dict['time_end_image'], 
                    'label_image': query_dict['label_image'], 
                    'delta_filters': delta_filters, 
                    'label_sort': str(int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds())) + this_uuid,
            },
            ConditionExpression='attribute_not_exists(entry_id)'
        )
        print("dynamo put_item succeeded:")
        # print(json.dumps(response, indent=4))
    except ClientError as e:
        # Ignore the ConditionalCheckFailedException, bubble up other exceptions.
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise

def get_hops(rekog_label, id_filename, scan_index):
    table = dynamodb.Table(DYNAMO_MAIN)    
    exclusive_start_key = { 'id_type' : 'scenechange', 'id_filename': id_filename}
    response = table.query(
        IndexName=DYNAMO_MAIN_GSI,
        Limit=  1,
        ScanIndexForward=scan_index,
        ExclusiveStartKey=exclusive_start_key,
        KeyConditionExpression=Key('id_type').eq('scenechange'),
    )
    return response
def detect_hops(rekog_label, id_filename, scan_index):
    scenechange_threshold = 50
    prekog_continue = 1
    prekog_infinteloop = 0
    last_id_filename = id_filename
    last_hop = {}
    while prekog_continue > 0:
        prekog_continue = 0
        response = get_hops(rekog_label, last_id_filename, scan_index)
        if len(response['Items']) < 1:
            print('WARNING: items has less than 1: {} we are too fast lets sleep'.format(len(response['Items'])))
            prekog_continue += 1
            time.sleep(4)
        else:
            for this_item in response['Items']:
                # pprint(this_item)
                last_hop = this_item
                if last_id_filename == this_item['id_filename']:
                    print('WARNING: we got the same id_filename {} == {} BREAK!'.format(last_id_filename, this_item['id_filename']))
                    break
                else:
                     last_id_filename = this_item['id_filename']   
                for this_label in this_item['rekog_labels']:
                    if this_label['Name'] == rekog_label:
                        print('INFO: matched rekog_label: {} must go deeper \t{}:{};{}'.format(rekog_label, this_item['timestamp_minute'],this_item['timestamp_second'],this_item['timestamp_frame']))
                        prekog_continue += 1
                if int(this_item['scenedetect']) < scenechange_threshold:
                    print('INFO: scenedetect is too low {} must go deeper \t{}:{};{}'.format(int(this_item['scenedetect']), this_item['timestamp_minute'],this_item['timestamp_second'],this_item['timestamp_frame'] ))
                    prekog_continue += 1 
        prekog_infinteloop += 1
        if prekog_infinteloop > 15: 
            print('WARNING: infinteloop detected BREAK!')
            break
    pprint(last_hop)
    print('INFO: prekog_continue completed')
    return(last_hop)
    
def lambda_handler(event, context):
    get_environment_variables()  
    print('event: {}'.format(event))
    # print('S3_BUCKET: {}'.format(S3_BUCKET))
    print('DELTA_URL: {}'.format(DELTA_URL))
    print('DELTA_CONTENTNAME: {}'.format(DELTA_CONTENTNAME))
    # if S3_BUCKET == 'not-set':
    #     return 'ERROR: S3_BUCKET was not set'
    if DELTA_URL == 'not-set':
        return 'ERROR: DELTA_URL was not set'
    if DELTA_CONTENTNAME == 'not-set':
        return 'ERROR: DELTA_CONTENTNAME was not set'
    
    time.sleep(10)
    # rekog_label = 'Flyer'
    rekog_label = event['rekog_label']
    id_filename = event['id_filename']
    print('rekog_label: {} \tid_filename: {}'.format(rekog_label, id_filename))

    ## BACKWARDS in time
    if int(event['scenedetect']) > 50:
        print('first scene is {}, skipping hops_backwards'.format(event['scenedetect']))
        hops_backward = event
    else:
        hops_backward = detect_hops(rekog_label, id_filename, False)
    # pprint(hops_backward)
    print('hops_backward: {} {} {}'.format(hops_backward['timestamp_minute'],hops_backward['timestamp_second'],hops_backward['timestamp_frame'] ))

    ## FORWARD in time ( may have to wait for time to actually happen )
    hops_forward = detect_hops(rekog_label, id_filename, True)
    # pprint(hops_forward)
    print('hops_forward: {} {} {}'.format(hops_forward['timestamp_minute'],hops_forward['timestamp_second'],hops_forward['timestamp_frame']))

    query_dict = {}
    query_dict['label_image'] = id_filename
    query_dict['label'] = rekog_label
    query_dict['time_start'] = hops_backward['timestamp_minute']+ ':' + hops_backward['timestamp_second']
    query_dict['time_start_frame'] = str(hops_backward['timestamp_frame'])
    query_dict['time_start_image'] = hops_backward['id_filename']

    query_dict['time_end'] = hops_forward['timestamp_minute']+ ':' + hops_forward['timestamp_second']
    query_dict['time_end_frame'] = str(hops_forward['timestamp_frame'])
    query_dict['time_end_image'] = hops_forward['id_filename']
    pprint(query_dict)
    contentlist = delta_contents(DELTA_URL)
    # pprint(contentlist)
    for content in contentlist:
        if content['name'] == DELTA_CONTENTNAME:
            content_id = content['id']
            delta_info = delta_frameaccurateput(DELTA_URL, content_id, query_dict) 

    return 'SUCCESS: it ran'
