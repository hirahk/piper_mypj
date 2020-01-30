import time
import datetime
import os
from pymongo import MongoClient

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from my_module import my_functions

video_path = "./videos/"
thumb_path = "./thumbs/"

# Parameters for ECS
ecs_access_key_id = "your_ecs_access_key_id"
ecs_bucket_name = "your_ecs_bucket_name"

# Parameters for MongoDB
db_cred = 'your_admin_name:password'
db_host = 'your_db_host:port'
db_name = 'your_db_name'

# Get database connection with database name
client = MongoClient('mongodb://' + db_cred + '@' + db_host + '/' + db_name, retryWrites=False)
db = client[db_name]

dic_modified_time = {}

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        if os.path.splitext(event.src_path)[-1].lower() in ('.mp4'):
            # Get modification flag and time with monitoring mp4 files
            dic_modified_time[event.src_path] = datetime.datetime.now()

def folder_scan():
    temp_dic = dic_modified_time.copy()
    for file_path in temp_dic.keys():
        try:
            # If deltatime is greater than 3secs copy operation is finished
            if (datetime.datetime.now() - dic_modified_time[file_path]).total_seconds() > 3:
                del dic_modified_time[file_path]
                if os.path.isdir(video_path):
                    # directoryだったら中のファイルに対して再帰的にこの関数を実行
                    files = os.listdir(video_path)
                    for filename in files:
                        thumbfile = my_functions.create_thumbnail(video_path, thumb_path, filename, 10)
                        visitor = my_functions.detect_visitor(thumb_path, thumbfile)
                        print("Visitor:" + visitor)
                        my_functions.upload_to_ECS(video_path, filename, "video/mp4", "public-read")

                        strdate = filename.rsplit(".",1)[0]
                        thumbfile = strdate + "-thumb.jpg"
                        capture_date = datetime.datetime.strptime(strdate,"%Y%m%d%H%M%S")
                        comments = "来訪者：" + visitor
                        video_url = "http://" + ecs_access_key_id.split('@')[0] + ".public.ecstestdrive.com/" + ecs_bucket_name + "/" + filename
                        thumbnail_url = "http://" + ecs_access_key_id.split('@')[0] + ".public.ecstestdrive.com/" + ecs_bucket_name + "/" + thumbfile
                        # Insert form fields into database            
                        db.photos.insert_one({'date':capture_date, 'comments':comments, 'video':video_url, 'thumb':thumbnail_url})

                        my_functions.slack_notify(visitor)

                    # for file in files:
                        os.remove(video_path + filename)

                if os.path.isdir(thumb_path):
                    # directoryだったら中のファイルに対して再帰的にこの関数を実行
                    files = os.listdir(thumb_path)
                    for filename in files:
                        # print(file)
                        my_functions.upload_to_ECS(thumb_path, filename, "image/jpeg", "public-read")
                    # for file in files:
                        os.remove(thumb_path + filename)

                print("Operation completed")

        except Exception as e:
            print(e)
            # Continue process with error occurence
            continue

if __name__ == "__main__":
    print("Folder scan started...")
    
    while 1:
        event_handler = ChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, video_path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
                folder_scan()
                
        except KeyboardInterrupt:
            observer.stop()
        observer.join()