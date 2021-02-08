
__author__ = ["Jerry Xu"]
__credits__ = ["Ethan Mendes", "Jerry Xu", "Matthew Ding", "Jason Liang", "David Towers"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Ethan Mendes"
__email__ = "eamendes88@gmail.com"
__status__ = "Prototype"

import math
import json
import requests
import os


# GET requests to TomTom API are made using this package: https://2.python-requests.org/en/master/

def round(value, up):
	if up == 1:
		value = float(int(math.ceil(value * 1000))) / 1000
		return value
	else:
		value = float(int(math.floor(value * 1000))) / 1000
		return value


def main():
	""" Main method to maintain terminal application allowing user to create a JSON file with desired stores in
	a bounding box

	"""
	API_PRIVATE = os.environ.get("TOM_TOM_PRIVATE")
	print("Please enter your desired filename (file will be JSON, do not leave blank): ")
	fileName = str(input())
	fileName = fileName.strip()
	if len(fileName) == 0:
		fileName = str('blank')

	fileWriter = open(fileName + '.json', 'w')

	print("Please enter your API key (leave blank for default): ")
	API_PRIVATE = str(input())
	API_PRIVATE = API_PRIVATE.strip()

	if len(API_PRIVATE) == 0:
		apiKey = str('KOlZazpVGjznzL2TJzBoJcOqNmxpVuGz')


	# coordinates of bounding box
	farWest = -73.508
	farEast = -69.928
	farNorth = 42.886
	farSouth = 41.237


	ewDivLength = 0.19
	nsDivLength = 0.33

	ewDivNum = int(math.ceil((farEast - farWest) / ewDivLength))
	nsDivNum = int(math.ceil((farNorth - farSouth) / nsDivLength))

	if ewDivNum > 50:
		ewDivNum = 50
		ewDivLength = round((farEast - farWest) / ewDivNum, True)

	if nsDivNum > 15:
		nsDivNum = 15
		nsDivLength = round((farNorth - farSouth) / nsDivNum, True)



	apiParameters = {
		'key': API_PRIVATE,
		'typeahead': True,
		'limit': 100,
		'ofs': 0,
		'countrySet': 'US',
		'topLeft': '',
		'btmRight': '',
		'categorySet': '9361023, 7332005, 9361066, 9361051, 9361009'
	}
	apiQuery = str('https://api.tomtom.com/search/2/categorySearch/.json');


	isExhausted = [[0 for EW in range(ewDivNum)] for NS in range(nsDivNum)]
	globalExhausted = False
	apiCallSafe = True

	totalCallCount = 0
	totalDataCount = 0
	totalGlobalCount = -1
	data = {}
	data['summary'] = []
	data['summary'].append({
		'numResults': totalDataCount
	})
	data['results'] = []

	fileWriter.write(json.dumps(data, sort_keys=True, indent=4))

	while (not globalExhausted) and apiCallSafe:
		fileWriter = open(fileName + '.json', 'w+')
		fileWriter.write(json.dumps(data, sort_keys=True, indent=4))
		globalExhausted = True
		totalGlobalCount += 1
		if totalGlobalCount == 19 :
			apiCallSafe = False
		for EW in range(ewDivNum):
			localWest = farWest + EW * ewDivLength
			localEast = farWest + (EW + 1) * ewDivLength
			for NS in range(nsDivNum):
				if isExhausted[NS][EW]:
					continue

				localSouth = farSouth + NS * nsDivLength
				localNorth = farSouth + (NS + 1) * nsDivLength

				topLeftStr = str(round(localNorth, 3)) + ", " + str(round(localWest, 3))
				btmRightStr = str(round(localSouth, 3)) + ", " + str(round(localEast, 3))

				apiParameters['topLeft'] = topLeftStr
				apiParameters['btmRight'] = btmRightStr
				apiParameters['ofs'] = totalGlobalCount * 100

				response = requests.get(apiQuery, params=apiParameters)
				while True:
					try:
						jsonResponse = response.json()
						break
					except:
						response = requests.get(apiQuery, params=apiParameters)

				if jsonResponse['summary']['totalResults'] > jsonResponse['summary']['numResults'] + \
						jsonResponse['summary'][
							'offset']:
					globalExhausted = False
				else:
					isExhausted[NS][EW] = True

				for eachStore in jsonResponse['results']:
					data['results'].append(eachStore)
					totalDataCount += 1
					for sumData in data['summary']:
						sumData['numResults'] = totalDataCount

				totalCallCount += 1

				print(totalDataCount)
				if totalCallCount > 1000:
					apiCallSafe = False

	print(ewDivNum)
	print(nsDivNum)
	print('\n\n')
	print(totalDataCount)
	print(totalCallCount)
	fileWriter.write(json.dumps(data, sort_keys=True, indent=4))

main()
