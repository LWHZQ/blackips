import pymongo

mongo_client = pymongo.MongoClient(host="192.168.11.135", port=27017, connect=False)
mongo_collection = mongo_client["podding"]["black_ip"]