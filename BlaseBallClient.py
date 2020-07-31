import requests
import socketio
import datetime
import json
from DBConnectors import *

class BlaseBallClient:
	def __init__(self, db_connector):
		self.base_url = 'https://blaseball.com/'#could've called it "blase_url", but want to keep this clean
		self.session = requests.Session()
		with open ('initialState.json', 'r') as last_scores_file:
			self.last_scores = json.loads(last_scores_file.read())
		self.dbc = db_connector
		self.sio = self.setup_socket()
	
	def setup_socket(self):
		sio = socketio.Client()
		@sio.event
		def connect():
			print('connection established')
			
		@sio.on('gameDataUpdate')
		def on_message(data):
			received = datetime.datetime.utcnow()
			schedule_types = ('schedule', 'tomorrowSchedule')
			for object_type in data.keys():
				if object_type in self.last_scores:
					if object_type in schedule_types:
						for event in data[object_type]:
							game_id = event['_id']
							game_found = False
							for old_event in self.last_scores[object_type]:
								if game_id == old_event['_id']:
									game_found = True
									if event != old_event:
										print(event['lastUpdate'])
										self.dbc.add_entry('event', {'record': event, 'received': received})
									break
							if not game_found:
								self.dbc.add_entry('event', {'record': event, 'received': received})
					elif object_type == 'sim':
						if any(data[object_type].get(key) != self.last_scores[object_type].get(key) for key in data[object_type].keys() if key != 'day'):
							self.dbc.add_entry(object_type, {'record': data[object_type], 'received': received})
					else:
						if data[object_type] != self.last_scores[object_type]:
							self.dbc.add_entry(object_type, {'record': data[object_type], 'received': received})
				else:
					print('New field in gameDataUpdate:', object_type)
					#If it's type that wasn't in the last one, record it
					if object_type in schedule_types:
						self.dbc.add_entries('event', [{'record': record, 'received': received} for record in data[object_type]])
					else:
						self.dbc.add_entry(object_type, {'record': data[object_type], 'received': received})
			self.last_scores = data
		
		@sio.event
		def disconnect():
			print('disconnected from sio')
		
		return sio
	
	def login(self, username, password):
		try:
			self.session.post(f'{self.base_url}auth/local', json={'isLogin': True, 'username': username, 'password': password})
		except:
			#TODO: Get good error handling
			print('Error on login')
	
	def save_last_scores(self):
		with open ('initialState.json', 'w') as last_scores_file:
			json.dump(self.last_scores, last_scores_file)
	
	#Database Calls
	def get_db_item(self, type, id=None):
		try:
			if isinstance(id, list):
				return self.session.get(f'{self.base_url}database/{type}', params={'ids': ','.join(id)}).json()
			elif isinstance(id, str):
				return self.session.get(f'{self.base_url}database/{type}', params={'id': id}).json()
			else:
				return self.session.get(f'{self.base_url}database/{type}').json()
		except:
			#TODO: Get good error handling
			print('Error on get_db_item')
	
	def get_team(self, id):
		return self.get_db_item('team', id)
		
	def get_all_teams(self):
		return self.get_db_item('allTeams')
		
	def get_global_events(self):
		return self.get_db_item('globalEvents')
		
	def get_league(self, id):
		return self.get_db_item('league', id)
		
	def get_subleague(self, id):
		return self.get_db_item('subleague', id)
	
	def get_all_divisions(self):
		return self.get_db_item('allDivisions')
	
	def get_game(self, id):
		return self.get_db_item('gameById', id)
		
	def get_players(self, ids):
		return  self.get_db_item('players', ids)
	
	#Tracking Scores
	def track_scores(self):		
		try:
			self.sio.connect('wss://blaseball.com/socket.io/')
		except:
			#TODO: Error handling
			print("Couldn't keep connection to blaseball.com. Is it a siesta?")
			return 'Woops'
		
		def quit_question():
			x = True
			while x:
				x = input('Stop? ("Y" to stop): ') != 'Y'
				if not x:
					x = input('Confirm? ("Yes" to confirm):') != 'Yes'
			print('Stopping game tracker.')
			self.sio.disconnect()
		
		self.sio.start_background_task(quit_question)
		self.sio.wait()
		self.save_last_scores()