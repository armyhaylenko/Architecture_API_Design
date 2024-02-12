import datetime as dt

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://api-ninjas.com/api/jokes
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(location: str, date: dt.date):
    city, country = location.split(',')
    if not city or not country:
        raise InvalidUsage('Location must consist of city and country, separated by a comma!')

    url_base_url = (
        "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/_location/_date/_date?unitGroup=metric&key=_apikey&contentType=json")

    url = url_base_url.replace('_location', city.join(['%2C%20', country])).replace('_apikey', RSA_KEY).replace('_date', date.isoformat())

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        try:
            weather_data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise InvalidUsage('Response from the weather API was not JSON!', status_code=500)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)

    today = weather_data.get('days')[0]  # today
    weather_data = {
        "temp_c": today.get('temp'),
        "wind_kph": today.get('windspeed'),
        "pressure_mb": today.get('pressure'),
        "humidity": today.get('humidity'),
        "description": today.get('description')
    }
    return weather_data


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Mykhailenko: python weather app.</h2></p>"


@app.route("/api/v1/weather/today", methods=["POST"])
def weather_today():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    requester_name = json_data.get("requester_name")

    if not requester_name or len(str(requester_name).split(' ')) != 2:
        raise InvalidUsage("Expected full name to be provided!", status_code=400)

    location = json_data.get("location")

    if not location:
        raise InvalidUsage("Expected location to be provided!", status_code=400)

    date = json_data.get("date")

    if not date:
        raise InvalidUsage("Expected date to be provided!", status_code=400)
    try:
        date = dt.date.fromisoformat(date)
    except TypeError:
        raise InvalidUsage("Date provided is not ISO-formatted!", status_code=400)

    weather = get_weather(location, date)

    end_dt = dt.datetime.now()

    result = {
        "event_start_datetime": start_dt.isoformat(),
        "event_finished_datetime": end_dt.isoformat(),
        "event_duration": str(end_dt - start_dt),
        "requester_name": requester_name,
        "timestamp": start_dt.isoformat(),
        "location": location,
        "date": date.isoformat(),
        "weather": weather,
    }

    return result
