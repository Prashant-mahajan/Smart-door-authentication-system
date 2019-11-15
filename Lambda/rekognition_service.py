import json
import random
import base64
import boto3

import cv2

def upload_unknown_frame_to_s3(fileName):
        kvs_client = boto3.client('kinesisvideo')
        kvs_data_pt = kvs_client.get_data_endpoint(
            StreamARN='arn:aws:kinesisvideo:us-west-2:040078798279:stream/LiveRekognitionVideoAnalysisBlog/1573772702784', # kinesis stream arn
            APIName='GET_MEDIA'
        )
        
        print(kvs_data_pt)
        
        end_pt = kvs_data_pt['DataEndpoint']
        kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt, region_name='us-west-2') # provide your region
        kvs_stream = kvs_video_client.get_media(
            StreamARN='arn:aws:kinesisvideo:us-west-2:040078798279:stream/LiveRekognitionVideoAnalysisBlog/1573772702784', # kinesis stream arn
            StartSelector={'StartSelectorType': 'NOW'} # to keep getting latest available chunk on the stream
        )
        print(kvs_stream)
    
        with open('/tmp/stream.mkv', 'wb') as f:
            streamBody = kvs_stream['Payload'].read(1024*16384) # reads min(16MB of payload, payload size) - can tweak this
            f.write(streamBody)
            # use openCV to get a frame
            cap = cv2.VideoCapture('/tmp/stream.mkv')
    
            # use some logic to ensure the frame being read has the person, something like bounding box or median'th frame of the video etc
            ret, frame = cap.read() 
            cv2.imwrite('/tmp/frame.jpg', frame)
            s3_client = boto3.client('s3')
            s3_client.upload_file(
                '/tmp/frame.jpg',
                'unknown-users-images', # replace with your bucket name
                fileName
            )
            cap.release()

def lambda_handler(event, context):
    
    matched_faces = []
    print("here")
    for record in event['Records']:
      payload = json.loads(base64.b64decode(record["kinesis"]["data"]))
      print(payload)
      if "FaceSearchResponse" in payload:
          for face in payload["FaceSearchResponse"]:
                if "MatchedFaces" in face and len(face["MatchedFaces"]) > 0:
                    matched_faces.append(face["MatchedFaces"][0]["Face"]["FaceId"])
                    # Code to send OTP to user goes here.....
                elif "MatchedFaces" in face and len(face["MatchedFaces"]) == 0:
                    fileName = str(random.randint(0,10000)) + 'frame.jpg'
                    upload_unknown_frame_to_s3(fileName)
                    print(fileName)
                    #Code to send message to owner goes here....
                   
    return {
        'statusCode': 200,
        'body': json.dumps(matched_faces)
    }
    
