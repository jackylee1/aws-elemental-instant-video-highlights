from urllib2 import urlopen as wget
import urllib
import datetime
import os
import stat
from pprint import pprint
import json
from decimal import Decimal
import boto3
import time
from threading import Thread
import botocore
from botocore.client import ClientError
from boto3.dynamodb.conditions import Key, Attr
import uuid

## These are unique and must be set
S3_BUCKET = "not-set"
HLS_URL = 'not-set'

## hardcoded for console use
DYNAMO_MAIN = "catfinder5000-main"
DYNAMO_LIST = "catfinder5000-list"
DYNAMO_SUMMARY = "catfinder5000-summary"
DYNAMO_SUMMARY_GSI = 'rekog_type-timestamp_updated-index'
LAMBDA_PREKOG = "catfinder5000-prekog"
REKOG_LABEL = "Cat"

FFPROBE = './ffprobe'
FFMPEG = './ffmpeg'

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client("rekognition")
lambda_client = boto3.client('lambda')


def get_environment_variables():
    global S3_BUCKET
    global HLS_URL
    global DYNAMO_MAIN
    global DYNAMO_LIST
    global DYNAMO_SUMMARY
    global DYNAMO_SUMMARY_GSI
    global LAMBDA_PREKOG
    global REKOG_LABEL

    if os.environ.get('S3_BUCKET') is not None:
        S3_BUCKET = os.environ['S3_BUCKET']
        print('environment variable S3_BUCKET was found: {}'.format(S3_BUCKET))
    if os.environ.get('DYNAMO_MAIN') is not None:
        DYNAMO_MAIN = os.environ['DYNAMO_MAIN']
        print('environment variable DYNAMO_MAIN was found: {}'.format(DYNAMO_MAIN))
    if os.environ.get('DYNAMO_LIST') is not None:
        DYNAMO_LIST = os.environ['DYNAMO_LIST']
        print('environment variable DYNAMO_LIST was found: {}'.format(DYNAMO_LIST))
    if os.environ.get('DYNAMO_SUMMARY') is not None:
        DYNAMO_SUMMARY = os.environ['DYNAMO_SUMMARY']
        print('environment variable DYNAMO_SUMMARY was found: {}'.format(DYNAMO_SUMMARY))
    if os.environ.get('DYNAMO_SUMMARY_GSI') is not None:
        DYNAMO_SUMMARY_GSI = os.environ['DYNAMO_SUMMARY_GSI']
        print('environment variable DYNAMO_SUMMARY_GSI was found: {}'.format(DYNAMO_SUMMARY_GSI))
    if os.environ.get('LAMBDA_PREKOG') is not None:
        LAMBDA_PREKOG = os.environ['LAMBDA_PREKOG']
        print('environment variable LAMBDA_PREKOG was found: {}'.format(LAMBDA_PREKOG))
    if os.environ.get('HLS_URL') is not None:
        HLS_URL = os.environ['HLS_URL']
        print('environment variable HLS_URL was found: {}'.format(HLS_URL))
    if os.environ.get('REKOG_LABEL') is not None:
        REKOG_LABEL = os.environ['REKOG_LABEL']
        print('environment variable REKOG_LABEL was found: {}'.format(REKOG_LABEL))

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def get_url(url, time = 20):
    try:
        output = wget(url, timeout = time).read()
    except urllib2.HTTPError, e:
        print(e.code)
        error_message = e.code
        print(error_message )
    except urllib2.URLError, e:
        print(e.args)
        error_message = e.args
        print( error_message )
    else:
        return output
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_file(name, data):
    f = open(name, 'w+')
    f.write(data)
    f.close()

def delete_file(myfile):
    if os.path.isfile(myfile):
        os.remove(myfile)
        # print("Success: %s file was deleted" % myfile)
    else:    ## Show an error ##
        print("Error: %s file not found" % myfile)

def update_dyanmo_summary ( rekog_summary ):
    ## DynamoDB Update
    print("put_dynamo to table: " + str(DYNAMO_SUMMARY))
    table = dynamodb.Table(DYNAMO_SUMMARY)    # current
    response = table.update_item(
        Key={
            'rekog_label': rekog_summary['rekog_label'],
        },
        UpdateExpression="set timestamp_updated = :timestamp_updated, timestamp_ttl = :timestamp_ttl, rekog_type = :rekog_type, id_filename = :id_filename  ",
        ExpressionAttributeValues={
                ':timestamp_updated': rekog_summary['timestamp_updated'],
                ':timestamp_ttl': rekog_summary['timestamp_ttl'],
                ':rekog_type': rekog_summary['rekog_type'],
                ':id_filename': rekog_summary['id_filename'],
        },
        # ConditionExpression="job_state <> :completed",
        ReturnValues="UPDATED_NEW"
    )
    print("dynamo update_item succeeded: {}".format(response))
    # pprint(response)

def put_dynamo_main(dynamo_object):
    print("put_dynamo to table: " + str(DYNAMO_MAIN))
    table = dynamodb.Table(DYNAMO_MAIN)
    try:
        response = table.put_item(
            Item=dynamo_object,
            ConditionExpression='attribute_not_exists(id_filename)'
        )
        print("dynamo put_item succeeded: {}".format(response))
    except ClientError as e:
        # Ignore the ConditionalCheckFailedException, bubble up other exceptions.
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise

def invoke_lambda(dynamo_object):
    invoke_response = lambda_client.invoke(FunctionName=LAMBDA_PREKOG,  InvocationType='Event', Payload=json.dumps(dynamo_object, cls=DecimalEncoder))
    print("invoke: {}".format(dynamo_object))
    print("invoke " + str(LAMBDA_PREKOG) + " code: " + str(invoke_response['StatusCode']))

def parse_manifest(url_full):  
    master_ttl = 3600

    # PARSE manifest
    print("master manifest: " + url_full)

    # wrangle the urls
    base_url = '/'.join(url_full.split('/')[:-1]) + '/'
    print("baseurl: {}".format(base_url))
    filename_master = url_full.split('/')[-1]
    print("filename_master: {}".format(filename_master))

    # GET master manifest
    string_master = get_url(base_url + filename_master)
    print("string_master: {}".format(string_master))

    # PARSE frame rate for the segments
    segment_framerate = float(string_master.split('FRAME-RATE=')[1].split('\n')[0])
    print("segment_framerate: {}".format(segment_framerate))

    # PARSE the m3u8 child manifestss. Returns list of these strings
    filename_playlists = [x for x in string_master.split('\n') if '.m3u8' in x]
    print("filename_playlists: {}".format(filename_playlists))

    # GET child manifest
    string_playlist = get_url(base_url + filename_playlists[0])
    # print("string_playlist: {}".format(string_playlist))

    # PARSE list of DATE-time and segment name and get last one
    segment_datetime = ''
    # segment_duration = ''
    segment_filename = ''
    for x in string_playlist.split('#EXT-X-PROGRAM-DATE-TIME:'):
        if '.ts' in x:
            segment_datetime = x.split('\n#EXTINF')[0]
            segment_duration = x.split('#EXTINF:')[1].split(',\n')[0]
            segment_filename = x.split('#EXTINF:')[1].split(',\n')[1].split('\n')[0]
    print('segment_datetime: {}'.format(segment_datetime))
    print('segment_duration: {}'.format(segment_duration))
    print('segment_filename: {}'.format(segment_filename))

    # get date time string without decimal 
    datetime_full = segment_datetime.split('.')[0] + 'Z'
    print('datetime_full: {}'.format(datetime_full))

    # get datetime object from date time string without decimal
    datetime_datetime = datetime.datetime.strptime(datetime_full, "%Y-%m-%dT%H:%M:%SZ")
    print('datetime_datetime: {}'.format(datetime_datetime))

    # get epoch of datetime
    epoch = datetime.datetime(1970,1,1)
    datetime_epoch = (datetime_datetime - epoch).total_seconds()
    print('datetime_epoch: {}'.format(datetime_epoch))

    # get the decimal from the date time string 
    datetime_decimal = segment_datetime.split('.')[1].split('Z')[:-1]
    print('datetime_decimal: {}'.format(datetime_decimal[0]))

    # convert decimal to frame number 
    datetime_frame = int(round(int(datetime_decimal[0]) * segment_framerate / 1000, 3))
    print('datetime_frame: {}'.format(datetime_frame))

    # how many frames per segment 
    frames_total = int(round(float(segment_duration) * segment_framerate, 3))
    print('frames_total: {}'.format(frames_total))

    # get filenames assumption started
    filename_base = segment_filename.split('.ts')[0]
    print('filename_base: {}'.format(filename_base))

    ## set tmp directory
    tmpdir = '/tmp/' + str(uuid.uuid4()) + '/'
    ensure_dir(tmpdir)

    # get the physical segment file
    save_file(tmpdir + segment_filename, get_url(base_url + segment_filename))

    ### FFPROBE - get start PTS time
    output_ffprobe1 = os.popen(FFPROBE + ' ' + tmpdir + segment_filename + ' -v quiet -show_streams -of json ').read()
    ffprobe_json1 = json.loads(output_ffprobe1)
    start_time = ffprobe_json1['streams'][0]['start_time']
    print('start_time: {}'.format(start_time))

    ### FFPROBE - get scene change information
    output_ffprobe = os.popen(FFPROBE + ' -v quiet -show_streams -show_frames -of json -f lavfi "movie=' + tmpdir + segment_filename + ',select=gt(scene\,.1)"').read()
    ffprobe_json = json.loads(output_ffprobe)
    scenedetect = {}
    for f in ffprobe_json['frames']:
        this_time = float(f['pkt_pts_time']) - float(start_time)
        this_frame = int(round(this_time * 30 + 1, 0))
        this_percent = int(round(float(f['tags']['lavfi.scene_score']),2) * 100)
        print('\tframe this_time: {} \tthis_frame: {} \tthis_percent: {}%'.format(this_time, this_frame, this_percent))
        scenedetect[str(this_frame)] = this_percent
    # pprint(scenedetect)

    ## FFMPEG - generate a jpg for each frame
    output_ffmpeg = os.popen(FFMPEG + ' -hide_banner -nostats -loglevel error -y -i ' + tmpdir + segment_filename + ' -an -sn -vcodec mjpeg -pix_fmt yuvj420p -qscale 1 -b:v 2000 -bt 20M "' + tmpdir + filename_base + '-%03d.jpg"  > /dev/null 2>&1 ').read()
    # delete ts segment
    myfile = tmpdir + segment_filename
    delete_file(myfile)

    # roll file names to next second after total fps 
    x_frame = datetime_frame
    x_filename = 1

    ## Cycle through all frames
    for x in xrange(0, frames_total):
        if x_frame >= int(segment_framerate):
            x_frame = 0
            datetime_datetime = datetime_datetime + datetime.timedelta(seconds=1)
        dynamo_epoch = (datetime_datetime - epoch).total_seconds() + (x_frame * 0.01 )
        dynamo_minute = datetime_datetime.strftime("%Y-%m-%d %H:%M")
        dynamo_second = datetime_datetime.strftime("%S")
        dynamo_frame = str(x_frame)
        dynamo_filename = filename_base + '-' + str(x_filename).zfill(3) + '.jpg'

        dynamo_object = {}
        dynamo_object={
                'id_filename': dynamo_filename,
                'id_type': 'scenechange',
                'timestamp_minute': dynamo_minute,
                'timestamp_second': dynamo_second,
                'timestamp_frame' : dynamo_frame,
                'timestamp_epoch': Decimal(dynamo_epoch),
                'timestamp_created' : int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds()),
                'timestamp_ttl' : int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds() + master_ttl) # 2 hours
        }
        ## Check for Scene Detection on this frame
        if str(x_filename) in scenedetect:
            ## S3 upload
            data = open(tmpdir + dynamo_filename, 'rb')
            pprint(s3.Bucket(S3_BUCKET).put_object(Key=dynamo_filename, Body=data))

            dynamo_object['scenedetect'] = str(scenedetect[str(x_filename)])
            # dynamo_object['scenedetect_round'] = str(int(round(scenedetect[str(x_filename)], -1)))

            ## Run Rekog if scene change is above 10
            if scenedetect[str(x_filename)] > 10:
                ## REKOGNTION -- Labels
                print("starting rekog.... scenedetect is: " + str(scenedetect[str(x_filename)]))
                response = rekognition.detect_labels(Image={"S3Object": {"Bucket": S3_BUCKET, "Name": dynamo_filename}})
                rekog_labels_list = []
                person_ok = 0
                for obj in response['Labels']:
                    rekog_labels_list.append({'Confidence': str(int(round(obj['Confidence']))), 'Name': obj['Name']})
                    ## deltafa-summary
                    rekog_summary_dynamo = {}
                    rekog_summary_dynamo['scenedetect'] = str(scenedetect[str(x_filename)])
                    rekog_summary_dynamo['rekog_label'] = obj['Name']
                    rekog_summary_dynamo['rekog_type'] = 'label'
                    rekog_summary_dynamo['id_filename'] = dynamo_filename
                    rekog_summary_dynamo['timestamp_updated'] = int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds())
                    rekog_summary_dynamo['timestamp_ttl'] = int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds() + master_ttl )

                    if rekog_summary_dynamo['rekog_label'] == REKOG_LABEL:
                        # rekog_summary_dynamo['timestamp_minute'] = dynamo_minute,
                        # rekog_summary_dynamo['timestamp_second'] = dynamo_second,
                        # rekog_summary_dynamo['timestamp_frame'] = dynamo_frame,
                        # invoke_lambda(rekog_summary_dynamo)
                        dynamo_object['rekog_label'] = obj['Name']
                        invoke_lambda(dynamo_object)

                    if int(round(obj['Confidence'])) > 79:
                        update_dyanmo_summary(rekog_summary_dynamo)

                    if obj['Name'] == 'Person':
                        person_ok = 1
                rekog_labels = sorted(rekog_labels_list, key=lambda obj: obj['Confidence'])
                print('rekog labels: {}'.format(rekog_labels))
                dynamo_object['rekog_labels'] = rekog_labels

                ## REKOGNTION -- Celeb
                if person_ok == 1:
                    print("rekog found a Person, running celeb....")                
                    rekog_celebs = rekognition.recognize_celebrities(Image={"S3Object": {"Bucket": S3_BUCKET, "Name": dynamo_filename}})
                    if rekog_celebs['CelebrityFaces']:
                        print("rekog found a celeb...")
                        rekog_celebs_list = []
                        for obj in rekog_celebs['CelebrityFaces']:
                            # invoke_lambda( rekog_label_dynamo  ) 
                            ## deltafa-summary
                            rekog_summary_dynamo = {}
                            rekog_summary_dynamo['scenedetect'] = str(scenedetect[str(x_filename)])
                            rekog_summary_dynamo['rekog_label'] = obj['Name']
                            rekog_summary_dynamo['rekog_type'] = 'celeb'
                            rekog_summary_dynamo['id_filename'] = dynamo_filename
                            rekog_summary_dynamo['timestamp_updated'] = int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds())
                            rekog_summary_dynamo['timestamp_ttl'] = int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds() + master_ttl)
                            update_dyanmo_summary(rekog_summary_dynamo)

                        print('rekgo celeb: {}'.format(rekog_celebs_list))
                        dynamo_object['rekog_celebs'] = rekog_celebs_list
                    else:
                        print("rekog did NOT find celeb...")
                # PUT DYNAMO - main
                put_dynamo_main(dynamo_object)
        # clean up jpgs
        delete_file(tmpdir + dynamo_filename)

        x_frame += 1
        x_filename += 1    


def write_json():

    ## set tmp directory
    tmpdir = '/tmp/' + str(uuid.uuid4()) + '/'
    ensure_dir(tmpdir)

    print("query of table: " + str(DYNAMO_LIST))
    table = dynamodb.Table(DYNAMO_LIST)    
    response = table.query(
        Limit=30,
        ScanIndexForward=False,
        KeyConditionExpression=Key('label').eq(REKOG_LABEL),
    )
    json_string = json.dumps(response['Items'], cls=DecimalEncoder)
    dynamo_filename = 'list-vod.json'
    with open(tmpdir + dynamo_filename, 'w') as outfile:
        outfile.write(json_string)

    ## S3 upload
    data = open(tmpdir + dynamo_filename, 'rb')
    pprint(s3.Bucket(S3_BUCKET).put_object(Key=dynamo_filename, Body=data))

    rekog_type = 'label'
    print("query of table: " + str(DYNAMO_SUMMARY))
    table = dynamodb.Table(DYNAMO_SUMMARY)    
    response = table.query(
        Limit=30,
        IndexName=DYNAMO_SUMMARY_GSI,        
        ScanIndexForward=False,
        KeyConditionExpression=Key('rekog_type').eq(rekog_type),
    )
    json_string = json.dumps(response['Items'], cls=DecimalEncoder)
    dynamo_filename = 'list-' + rekog_type + '.json'
    
    with open(tmpdir + dynamo_filename, 'w') as outfile:
        outfile.write(json_string)
    ## S3 upload
    data = open(tmpdir + dynamo_filename, 'rb')
    pprint(s3.Bucket(S3_BUCKET).put_object(Key=dynamo_filename, Body=data))

    rekog_type = 'celeb'
    print("query of table: " + str(DYNAMO_SUMMARY))
    table = dynamodb.Table(DYNAMO_SUMMARY)    
    response = table.query(
        Limit=30,
        IndexName=DYNAMO_SUMMARY_GSI,        
        ScanIndexForward=False,
        KeyConditionExpression=Key('rekog_type').eq(rekog_type),
    )
    json_string = json.dumps(response['Items'], cls=DecimalEncoder)
    dynamo_filename = 'list-' + rekog_type + '.json'
    
    with open(tmpdir + dynamo_filename, 'w') as outfile:
        outfile.write(json_string)
    ## S3 upload
    data = open(tmpdir + dynamo_filename, 'rb')
    pprint(s3.Bucket(S3_BUCKET).put_object(Key=dynamo_filename, Body=data))

segment_duration = 9
def lambda_handler(event, context):
    get_environment_variables()  
    print('S3_BUCKET: {}'.format(S3_BUCKET))
    print('HLS_URL: {}'.format(HLS_URL))
    if S3_BUCKET == 'not-set':
        return 'ERROR: S3_BUCKET was not set'
    if HLS_URL == 'not-set':
        return 'ERROR: HLS_URL was not set'
        
    for i in range(7):
        print('starting thread: {}'.format(i))
        t = Thread(name='rekog', target=parse_manifest, args=(HLS_URL,))
        t.start()
        print('sleeping: {}'.format(segment_duration))
        time.sleep(segment_duration)
        w = Thread(name='json', target=write_json)
        w.start()
    return 'SUCCESS: it ran'
     