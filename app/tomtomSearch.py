
__author__ = ["Jerry Xu", "Ethan Mendes"]
__credits__ = ["Ethan Mendes", "Jerry Xu", "Matthew Ding", "Jason Liang", "David Towers"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Ethan Mendes"
__email__ = "eamendes88@gmail.com"
__status__ = "Prototype"

# GET requests to TomTom API are made using this package: https://2.python-requests.org/en/master/
import os
import requests
import urllib.parse

def geo(address):
    """ Method fetches the GPS coordinates for a particular address using the TomTom API

    :param address: entered user address
    :return: latitude and longitude of the address
    """
    API_PRIVATE = os.environ.get("TOM_TOM_PRIVATE")
    encoded = urllib.parse.quote(address)
    query ='https://api.tomtom.com/search/2/geocode/' + str(encoded) + '.json?limit=1&countrySet=US&lat=42&lon=-72&topLeft=42.886%2C%20-73.508&btmRight=41.237%2C-69.928&key=' + API_PRIVATE

    response = requests.get(query)
    while True:
        try:
            jsonResponse = response.json()
            break
        except:
            response = requests.get(query)

    latit = 0
    longit = 0

    for address in jsonResponse['results']:
        latit = address['position']['lat']
        longit = address['position']['lon']
    return latit, longit



def reverseGeo(latit, longit):
    """ Method returns the address from the GPS coordinates

    :param latit: latitude
    :param longit: longitude
    :return: plain English address
    """
    API_PRIVATE = os.environ.get("TOM_TOM_PRIVATE")
    query = 'https://api.tomtom.com/search/2/reverseGeocode/'+str(latit)+'%2C%20' +str(longit)+'.json?returnSpeedLimit=false&heading=0&radius=50&number=0&returnRoadUse=false&key=' + API_PRIVATE
    response = requests.get(query)
    while True:
        try:
            jsonResponse = response.json()
            break
        except:
            response = requests.get(query)

    cur_address = ''

    for address in jsonResponse['addresses']:
        cur_address = address['address']['freeformAddress']
    return cur_address


def search(latit, longit, dist, num_results):
    """ Method fetches stores within a certain distance from a location

    :param latit: the latitude of the location
    :param longit: the longitude of the location
    :param dist: the maximum searching distance from the location
    :param num_results: the number of results to return
    :return: list of latitudes and longitudes from found stores
    """
    API_PRIVATE = os.environ.get("TOM_TOM_PRIVATE")
    apiParameters = {
        'key': API_PRIVATE,
        'typeahead': True,
        'limit': num_results,
        'ofs': 0,
        'countrySet': 'US',
        'lat': latit,
        'lon': longit,
        'radius': dist,
        'categorySet': '9361023, 7332005, 9361066, 9361051, 9361009'
    }
    apiQuery = str('https://api.tomtom.com/search/2/categorySearch/.json');

    response = requests.get(apiQuery, params=apiParameters)
    while True:
        try:
            jsonResponse = response.json()
            break
        except:
            response = requests.get(apiQuery, params=apiParameters)

    latitude_lst = []
    longitude_lst = []
    for eachStore in jsonResponse['results']:
        latitude_lst.append(eachStore['position']['lat'])
        longitude_lst.append(eachStore['position']['lon'])
    final_lat = []
    final_lon = []
    for i in range(len(latitude_lst)):
        repeat = False
        for j in range(len(final_lat)):
            if final_lat[j] == latitude_lst[i] and final_lon[j] == longitude_lst[i]:
                repeat = True
                break
        if repeat == False:
            final_lat.append(latitude_lst[i])
            final_lon.append(longitude_lst[i])
    return final_lat, final_lon
