import json
import boto3
import rekognition_service
import dynamo_service
import rds_service
import notification_service
import time

s3_client = boto3.client('s3')
threshold = 85
# bucket_keys = ["asaggarw/aws_1.jpg", "asaggarw/aws_2.jpg", "aa6911/aws_1.jpg", "aa6911/aws_2.jpg", "aa6911/aws_3.jpg"]

def index_image(bucket_name, bucket_key, collection_id, timestamp, tagged, user_name, tagged_by):
    device_owner_id = bucket_key.split("/")[0]
    bucket_file_name = bucket_key.split("/")[1]
    print ('Bucket - %s' % bucket_name)
    print("Owner - %s" % device_owner_id)
    print ('Bucket File Name - %s' % bucket_key) 
    print ('User Name - %s' % user_name) 
    indexed_face_records = rekognition_service.index_face(collection_id, bucket_name, bucket_key)
    should_insert_image = False
    if indexed_face_records is None: 
        return None
    indexed_face_ids = []
    user_names = []
    unknown_user_count = 0
    for faceRecord in indexed_face_records:
        face_id = faceRecord['Face']['FaceId']
        indexed_face_ids.append(face_id)
        bounding_box = faceRecord['Face']['BoundingBox']
        height = bounding_box['Height']
        width = bounding_box['Width']
        top = bounding_box['Top']
        left = bounding_box['Left']
        bounding_box_str = ','.join(str(e) for e in [width, height, left, top])
        response = rekognition_service.search_collection_using_face_id(collection_id, threshold, face_id)
        if response is None:
            # create user for face and add in dynamo user table
            should_insert_image = True
            matched_user_id = "user-" + face_id
            unknown_user_count += 1
            rds_service.put_user_record(matched_user_id, device_owner_id, tagged, user_name, timestamp)
        else:
            matched_face_id = response[0]['Face']['FaceId']
            matched_user_id, last_seen, user_name_from_db = rds_service.get_user_id_for_image(matched_face_id, device_owner_id)
            if user_name_from_db is not None:
                user_names.append(user_name_from_db)
            else:
                unknown_user_count += 1
            if tagged_by == 'owner':
                rds_service.update_user_record(matched_user_id, device_owner_id, user_name, timestamp)
        # if should_insert_image:
        rds_service.put_face_record(face_id, matched_user_id, bucket_key, device_owner_id, bounding_box_str, timestamp, tagged_by)
    return True, user_names, unknown_user_count

def uploadPiImages(event, context):
    
    collection_id = 'MyCollection'
    
    # rekognition_service.delete_collection(collection_id)
    # rekognition_service.create_collection(collection_id)
    
    # bucket_name = "surveillance-cam"
    # bucket_key = "aa6911/rdj2.jpg"
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket_key = event["Records"][0]["s3"]["object"]["key"]
    print("Received bucket name[%s], bucket key[%s]" % (bucket_name, bucket_key))
    timestamp = str(time.time()).split(".")[0]
    print("Timestamp[%s] " % timestamp)

    response = s3_client.head_object(Bucket=bucket_name, Key=bucket_key)
    user_name = ""
    tagged = False
    metadata_field = 'tag'
    tagged_by = 'pi'
    if 'Metadata' in response and metadata_field in response['Metadata'] :
        tagged = True
        tagged_by = 'owner'
        user_name = response['Metadata'][metadata_field]
    print("User Name Received[%s]" % user_name)
    should_insert_image, user_names, unknown_user_count = index_image(bucket_name, bucket_key, collection_id, timestamp, tagged, user_name, tagged_by)
    if not tagged and should_insert_image and response is not None:
        recipient = "up293@nyu.edu"
        notification_service.send_email_with_s3(recipient, user_names, unknown_user_count, bucket_name, bucket_key)
    response = {
        "statusCode": 200,
        "body": "Success"
    }
    return response