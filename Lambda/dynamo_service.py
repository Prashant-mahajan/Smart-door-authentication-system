import boto3
import time

# device_owner_id_field = 
# face_id_field = 

def get_user_id_for_image(face_id, device_owner_id):
    print("Retrieve user id for face_id[" + face_id + "] and owner[" + device_owner_id + "]")
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('images_cc_proj')    
    try:
        response = table.get_item(
            Key={
                'face_id' : face_id,
            }
        )
    except Exception as e:
        print("Error in retrieving user id from face id")
        print(e.response['Error']['Message'])
        return None
    else :
        if 'Item' in response:
            item = response['Item']
            print ("Returning user id : {} for input face_id id : {}".format(item['user_id'], face_id))
            return item['user_id']
    print("No Users Found")
    return None
    
def put_face_record(face_id, user_id, path, device_owner_id):
    
    print("Inserting Face Record[" + str(face_id) + "] for user[" + str(user_id) + "], owner[" + str(device_owner_id) + "]")
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('images_cc_proj')    
    response = table.put_item(
        Item={
            'face_id' : face_id,
            'user_id': user_id,
            's3_path' : path,
            'owner_id' : device_owner_id,
        }
    )
    print("Insertion for Face Record Done")
    
def put_user_record(user_id, device_owner_id):
    
    print("Inserting User Record[" + user_id + "] for owner[" + device_owner_id + "]")
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('users_cc_proj')    
    response = table.put_item(
        Item={
            'user_id': user_id,
            'tagged' : False,
            'owner_id' : device_owner_id,
        }
    )
    print("Insertion for User Record Done")
    