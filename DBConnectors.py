from pymongo import MongoClient

class DBConnector():
	def __init__(self):
		pass
		
	def add_entry(self, table, entry):
		pass
		
	def add_entries(self, table, entries):
		for entry in entries:
			self.add_entries(table, entry)

class MongoDBConnector():
	def __init__(self, uri = 'mongodb://localhost:27017/', db_name = 'blaseball'):
		super().__init__()
		self.uri = uri
		self.mongo_client = MongoClient(self.uri)
		self.db = self.mongo_client[db_name]
	
	def add_entry(self, table, entry):
		self.db[table].insert_one(entry)
		
	def add_entries(self, table, entries):
		self.db[table].insert_many(entries)