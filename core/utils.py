from datetime import datetime, tzinfo
from dateutil.parser import parse
from django.db.models.base import ModelBase
from django.apps import apps
from json import dumps, loads
from django.contrib import messages
import pytz
from pprint import pprint
from django.shortcuts import render
from bootstrap_tracking.settings import TIME_ZONE
import re
from django.contrib.auth.models import User
from bootstrap_tracking.settings import DEBUG

TZINFO = pytz.timezone(TIME_ZONE)

def CCtoString(st):
    st2 = " ".join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', st))
    st3 = st2 if st2 else st
    return st3.title()


def astz(dt):
    assert isinstance(dt, datetime)
    return dt.astimezone(TZINFO)

def dbprint(*args):
    if DEBUG:
        print("----------")
        for arg in args:
            pprint(arg)
        print("----------")

def get_job_log(job):
    log = job.entry_set.all().order_by("-id")
    
    displayLog = []
    sameOp = True
    for i, entry in enumerate(log):
        op_id = entry.operation.op_id if entry.operation else "-"
        try:
            if op_id != log[i-1].operation.op_id:
                sameOp = not sameOp
        except ValueError:
            pass
        except AttributeError:
            pass
            
        displayLog.append([displayDT(entry.dt), op_id, entry.message, sameOp] )
    
    return displayLog

def alert_subscribe(username, locList):
    user = User.objects.get(username=username)
    user.last_name = dumps(locList)
    user.save()
    return loads(user.last_name)



def create_confirm_modal(request, name="confirm_modal", title="Title", message="Message", message_bottom="", table=None, data={}, action="Confirm", **kwargs):

    extra = {k: v for k,v in kwargs.items() if isinstance(v, str)}

    modalDict = {
        "name": name,
        "message": message,
        "title": title,
        "table": table,
        "data": dumps(data),
        "message_bottom": message_bottom,
        "action": action
    }
    

    messages.info(request, dumps({**modalDict, **extra}), extra_tags="modal_confirm")

def create_interim_op(obj):
    Location = apps.get_model("core", "Location")
    Operation = apps.get_model("core", "Operation")
    obj.is_interim = True
    obj.insp_bool = False
    obj.location = Location.objects.get(loc_id=Location.INTERIM)
    obj.op_note = "Operation added automatically"
    obj.name = "Interim inspection for {}".format(str(obj.op_id))
    obj.end_time = None
    obj.start_time = None
    obj.planned_run = None
    obj.planned_set = None
    obj.worker = None
    obj.status = Operation.PENDING
    obj.phase = Operation.NONE
    obj.save()

def stdDateTime(dt=None):
    if dt == None or dt == "now":
        dt = datetime.now(tz=pytz.utc).astimezone(TZINFO)
    elif isinstance(dt, str):
        dt = parse(dt).astimezone(TZINFO)
        #dt.replace(tzinfo=TZINFO)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def displayDT(dt):
    return astz(dt).strftime("%d/%m/%y %H:%M")

def minutesSince(time):
    if isinstance(time, str):
        time = parse(time)
  
    delta = datetime.now(tz=pytz.utc).astimezone(TZINFO) - time
    return round(delta.total_seconds()/60, 2)

def get_verbose(model, field_str, app="core"):
    try:
        if "__" in field_str:
            parent_str, field_str = field_str.split("__", 1)
            parent_model = apps.get_model(app, parent_str.replace("_id", ""))
            return get_verbose(parent_model, field_str, app="core")
        else:
            return model._meta.get_field(field_str).verbose_name
    except:
        return "views.get_verbose error"


def get_value(object, field_str):
    try:
        if "__" in field_str:
            parent_str, field_str = field_str.split("__", 1)
            # parent = job_id, field = "quantity"
            parentObj = getattr(object, parent_str.replace("_id", ""))
            val = get_value(parentObj, field_str)
            if isinstance(val, datetime):
                return val.astimezone(TZINFO)
            else:
                return val
        else:
            return getattr(object, field_str)
    except AttributeError:
        return "-"


def get_datatable(fieldDict, query, model):
    for field_str in fieldDict.keys():
        if "verbose" not in fieldDict[field_str]:
            fieldDict[field_str]["verbose"] = get_verbose(model, field_str)

    linkFields = [v.get("href") for v in fieldDict.values() if v.get("href")]
    queryFields = list(fieldDict.keys()) + linkFields

    queryData = list(query.values(*[f for f in queryFields if "__" not in f]))

    for i in range(len(queryData)):
        for field in [f for f in queryFields if "__" in f]:
            queryData[i][field] = get_value(query[i], field)

        for field in queryData[i].keys():
            if type(queryData[i][field]) is datetime:
                queryData[i][field] = displayDT(queryData[i][field])

    return fieldDict, queryData

def get_singletable(fieldDict, object, model):
    linkFields = [v.get("href")
                for v in fieldDict.values() if v.get("href")]
    opData = {f: get_value(object, f)
            for f in list(fieldDict.keys()) + linkFields}

    for k in opData.keys():
        if type(opData[k]) is datetime:
            opData[k] = displayDT(opData[k])
        
    for field_str in fieldDict.keys():
        if "verbose" not in fieldDict[field_str]:
            fieldDict[field_str]["verbose"] = get_verbose(
                model, field_str)
            
    return fieldDict, opData