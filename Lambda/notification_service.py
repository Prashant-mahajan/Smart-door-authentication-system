from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import boto3

SENDER = "Smart Surveillance Cam <ashim.agg93@gmail.com>"
AWS_REGION = "us-east-1"
SUBJECT = "Someone is at your door"
ses_client = boto3.client('ses',region_name=AWS_REGION)
s3_client = boto3.client('s3', 'us-west-2')

msg = "You have %s known persons at your doorstep."
msg1 = "You have %s unknown persons at your doorstep."
msg2 = "Please login to your dashboard to see more details or tag an unknown face."


def send_email_with_s3(recipient, user_names, unknown_user_count, bucket_name, bucket_key):
    
    device_owner_id = bucket_key.split("/")[0]
    bucket_file_name = bucket_key.split("/")[1]
    print ('Recevied request to send email for Bucket[%s], Owner[%s], Bucket_key[%s] To [%s]' \
    %  (bucket_name, device_owner_id, bucket_key, recipient))
    msg = MIMEMultipart()
    new_body = ""
    if len(user_names) > 0:
        new_body += ("You have %s known persons at your doorstep." % len(user_names) + '\n')
        for name in user_names:
            new_body += (name + "\n")
    if unknown_user_count > 0:
        new_body += ("You have %s unknown persons at your doorstep." % unknown_user_count)
        
    text_part = MIMEText(new_body, _subtype="html")
    msg.attach(text_part)
    msg["To"] = recipient
    msg["From"] = SENDER
    msg["Subject"] = SUBJECT
    s3_object = s3_client.get_object(Bucket = bucket_name, Key = bucket_key)
    body = s3_object['Body'].read()
    part = MIMEApplication(body, bucket_file_name)
    part.add_header("Content-Disposition", 'attachment', filename = bucket_file_name)
    msg.attach(part)
    try:
        response = ses_client.send_raw_email(RawMessage={"Data" : msg.as_bytes()})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print ('Completed request to send email for Bucket[%s], Owner[%s], Bucket_key[%s] To [%s]' \
    %  (bucket_name, device_owner_id, bucket_key, recipient))
        
        