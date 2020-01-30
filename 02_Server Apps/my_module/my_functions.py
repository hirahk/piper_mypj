import boto3
import cv2
import os
import requests
import json
from PIL import Image
from datetime import datetime

def upload_to_ECS(path, file, contenttype, acl):

    ecs_endpoint_url = "https://object.ecstestdrive.com"
    ecs_access_key_id = "your_ecs_access_key_id"
    ecs_secret_access_key = "your_ecs_secret_access_key"
    ecs_bucket_name = "your_ecs_bucket_name"

    print("Upload to ECS: " + file)

    s3 = boto3.resource("s3",
    endpoint_url = ecs_endpoint_url,
    aws_access_key_id = ecs_access_key_id,
    aws_secret_access_key = ecs_secret_access_key)

    s3.Bucket(ecs_bucket_name).upload_file(path + file, file,
    ExtraArgs={"ContentType": contenttype, "ACL": acl})

    print("Done")

def create_thumbnail(vpath, tpath, file, frame_num):
    # Return val: visitor
    cap = cv2.VideoCapture(vpath + file)
    if not cap.isOpened():
        return

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()

    if ret:
        tmpfile = file.rsplit(".",1)[0] + ".jpg"
        cv2.imwrite(tpath + tmpfile, frame)

    size = 225, 225
    with open(tpath + tmpfile, "rb") as f:
        img = Image.open(f)
        img.thumbnail(size)
        thumbfile = file.rsplit(".",1)[0] + "-thumb.jpg"
        img.save(tpath + thumbfile,"JPEG")
        img.close()
        print("Created thumbnail: " + thumbfile)
        f.close()
        os.remove(tpath + tmpfile)
        return thumbfile

def detect_visitor(tpath, file):
    # Return val: thumbfile

    aws_region = "ap-northeast-1"
    aws_access_key = "your_aws_access_key"
    aws_secret_key = "your_aws_secret_key"

    family_name = ["お父さん", "お母さん", "くるみ"]
    bb_top = [0.43, 0.34, 0.46]

    with open(tpath + file, "rb") as f1:
        with open("./sample/family.jpg", "rb") as f2:

            client = boto3.client("rekognition", region_name = aws_region,
            aws_access_key_id = aws_access_key,
            aws_secret_access_key = aws_secret_key)
            source=f1.read()
            target=f2.read()
            response = client.compare_faces(
                SourceImage={
                    "Bytes": source
                },
                TargetImage={
                    "Bytes": target
                }

            )

    flag = response.get("FaceMatches")

    if flag != []:
        i = 0
        for bb in bb_top:
            if bb == round(response["FaceMatches"][0]["Face"]["BoundingBox"]["Top"],2):
                visitor = family_name[i]
                return visitor
            i+=1
    else:
        visitor = "知らない人"
        return visitor

def slack_notify(who):

    WEB_HOOK_URL = "your_WEB_HOOK_URL"

    if who == "知らない人":
        fallback = "誰か来たよ！"
        color = "#EE0000"
        title = "誰か来たよ！ビデオに録画したよ！！"
    else:
        fallback = who + "が帰ってきたよ！"
        color = "#00EE00"
        title = who + "が帰ってきたよ！"

    requests.post(WEB_HOOK_URL, data = json.dumps({
        "username": u"見守りbot",
        "icon_emoji": u":robot_face:",
        "attachments": [
            {
                "fallback": fallback,
                "color": color,
                "pretext": "メッセージ",
                "title": title,
                "title_link": "your_PWS_app_url",
                "text": "ビデオを確認する\nyour_PWS_app_url",
                "ts": datetime.now().timestamp()
            }
        ]
    }))
