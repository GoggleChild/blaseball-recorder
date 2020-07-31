from BlaseBallClient import *
from DBConnectors import *

def main():
	bbc = BlaseBallClient(MongoDBConnector())
	bbc.track_scores()
	
if __name__ == '__main__':
	main()