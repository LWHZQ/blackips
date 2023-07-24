import pymongo
from  config import mongo_ip, mongo_port, mongo_db

mongo_client = pymongo.MongoClient(host=mongo_ip, port=mongo_port, connect=False)
mongo_collection = mongo_client[mongo_db]["black_ip"]