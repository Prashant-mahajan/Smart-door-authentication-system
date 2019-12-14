import json
import pickle
import boto3
import random

def save_and_send_message(notification_txt, face_id,otp, sns, table, number):
    item = {
    "temp_access_key" : str(otp),
    "face_id" : face_id
    }
    
    table.put_item(Item = item)
    # print("Done!!!!!")
    
    # Send your sms message.
    sns.publish(
        PhoneNumber=number,
        Message=notification_txt
    )

def lambda_handler(event, context):
    rekog_client = boto3.client('rekognition', region_name='us-west-2')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('visitors')
    table2 = dynamodb.Table('passcodes')
    sns = boto3.client('sns', region_name='us-west-2')
    
    name = event.get("username")
    number = event.get("usernumber")
    image_name = event.get("url").split("=")[-1]
    print(image_name)
    response=rekog_client.index_faces(CollectionId="rekVideoBlog",
                                Image={'S3Object':{'Bucket':"S3_BUCKET_NAME",'Name':image_name}},
                                ExternalImageId=image_name,
                                MaxFaces=1,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])
    
    face_id = response['FaceRecords'][0]['Face']['FaceId']
    
    item = {
        "FaceId": face_id,
        "Name" : name,
        "Phone number": number
    }
    
    table.put_item(Item=item)
    
    otp = random.randint(0,9999)
    notification_txt = 'Your OTP is {}'.format(otp)
    # send OTP
    save_and_send_message(notification_txt, face_id, otp, sns, table2, number)
    
    # TODO implement
    return {
        'statusCode': 200, 
        "Body" : "Added image to DB visitors"
    }
