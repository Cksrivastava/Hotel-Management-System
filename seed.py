from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["pg_db"]
rooms_collection = db["rooms"]

rooms_collection.delete_many({})

rooms = [
   
   If Need full code contact Himanshu For this
         @cksrivastava49@gmail.com
   
   
   
   ]

rooms_collection.insert_many(rooms)
print("Rooms inserted with images")
