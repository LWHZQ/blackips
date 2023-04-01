import pymongo

mongo_client = pymongo.MongoClient(host="192.168.11.135", port=27017, connect=False)
mongo_collection = mongo_client["podding"]["blackip"]

mongo_client1 = pymongo.MongoClient(host="192.168.11.234", port=27017, connect=False, username="podding", password="Podding_123", authSource="admin")
res = mongo_client1["newpodding"]["file"].find(
    {"processed_analysis.ip_and_uri_finder.summary":{'$gt':[]}},
    {"processed_analysis.ip_and_uri_finder.ipv4":1, "processed_analysis.ip_and_uri_finder.ipv6":1}
)
for i in res:
    ipv4 = i["processed_analysis"]["ip_and_uri_finder"].get("ipv4", "")
    for ip in ipv4:
        t = mongo_collection.find_one({"ip": ip})
        print(t)


