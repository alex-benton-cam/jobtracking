from jinja2 import Environment
from django.contrib import messages
from requests import session
import json
from datetime import datetime
import pytz

def from_json(value):
    return json.loads(value)

def unix(not_used):
    tz = pytz.timezone("Europe/London")    
    dif = datetime.now(tz=tz) - datetime.fromtimestamp(0, tz=tz)
    return dif.total_seconds()

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'get_messages': messages.get_messages,
        'request.session': session,
        })
    env.filters['from_json'] = from_json
    env.filters['unix'] = unix
    return env