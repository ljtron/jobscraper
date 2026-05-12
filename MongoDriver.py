import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.client = pymongo.MongoClient(host=str(os.getenv("DBSRV")))

    
    def test_connection(self):
        '''
            test_connection

            Description: 
            Is a function that tests the connection to the MongoDB database. 
            It uses the ping command to check if the connection is successful. 
            If the connection is successful, it prints a success message. 
            If the connection fails, it catches the exception and prints an error message.
        '''
        try:
            db = self.client.test
            print(db.command("ping"))
            if(db.command("ping")["ok"] == 1.0):
                print("Connected to MongoDB successfully!")
            else:
                raise Exception("Failed to connect to MongoDB.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    def insert_data(self, data, collection_name):
        '''
            insert_data

            Parameters:
            data (dict): The data to be inserted into the MongoDB collection.
            collection_name (str): The name of the MongoDB collection where the data will be inserted

            Description: 
            Is a function that inserts data into a specified collection in the MongoDB database. 
            It takes two parameters: data (the data to be inserted) and collection_name (the name of the collection where the data will be inserted). 
            It uses the insert_one method to insert the data into the collection. 
            If the insertion is successful, it prints a success message. 
            If the insertion fails, it catches the exception and prints an error message.
        '''
        try:
            db = self.client.jobs
            collection = db[collection_name]
            result = collection.insert_one(data)
            print(f"Data inserted successfully with id: {result.inserted_id}")
        except Exception as e:
            print(f"Failed to insert data into MongoDB: {e}")

    def find_data(self, query, collection_name):
        '''
            find_data

            Parameters:
            query (dict): The query to be used for finding data in the MongoDB collection.
            collection_name (str): The name of the MongoDB collection where the data will be searched.

            Description: 
            Is a function that finds data in a specified collection in the MongoDB database based on a given query. 
            It takes two parameters: query (the query to be used for finding data) and collection_name (the name of the collection where the data will be searched). 
            It uses the find method to search for data in the collection based on the provided query. 
            If the search is successful, it returns the found data. 
            If the search fails, it catches the exception and prints an error message.
        '''
        try:
            db = self.client.jobs
            collection = db[collection_name]
            results = collection.find(query)
            return list(results)
        except Exception as e:
            print(f"Failed to find data in MongoDB: {e}")
            return None

    def close_connection(self):
        '''
            close_connection

            Description: 
            Is a function that closes the connection to the MongoDB database. 
            It uses the close method to close the connection. 
            If the connection is closed successfully, it prints a success message. 
            If the connection fails to close, it catches the exception and prints an error message.
        '''
        try:
            self.client.close()
            print("MongoDB connection closed successfully!")
        except Exception as e:
            print(f"Failed to close MongoDB connection: {e}")


# if __name__ == "__main__":
#     client = MongoDBClient()
#     client.test_connection()
#     client.close_connection()