from core.models import *
from core.utils import *
from django.apps import AppConfig, apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import ModelBase
import re
# python manage.py shell
# exec(open("_test.py").read())

# For daphne server
# daphne -b 0.0.0.0 -p80 bootstrap_tracking.asgi:application

def attempt1():
    queryset = Operation.objects.all()
    job = Job.objects.get(work_no="W/21704")

    print(queryset.values("job_id__quantity"))
    print(job)

    displayFields = ["op_id", "job_id__quantity"]
    queryData = queryset.values(*displayFields)
    print(queryData["W/21704/A10"])

def attempt():
    
    print(apps.get_model('core', 'job'))
    print(type(apps.get_model('core', 'job')))
    print(get_verbose(Job, 'job_name'))
    print(get_verbose('job', 'job_name'))
    

def attempt2():
    displayFields = ["op_id", 
                    "job_id__company",
                    "job_id__job_name",
                    "part_no",
                    "job_id__quantity",
                    "drg_no"]

    operation = Operation.objects.get(link_slug="w21704a10")
    print(type(operation))
    print(operation.op_id)
    print(operation.job.quantity)
    print(operation.__dict__["op_id"])
    print(operation.job.__dict__["quantity"])
    print(getattr(operation, "op_id"))
    print(type(getattr(operation, "job")))
    
    # get_value(operation, "job_id__quantity"
    print(getattr(getattr(operation, "job"), "quantity"))
    #print(operation.values(*displayFields))
    
    
def attempt3():
            
    operation = Operation.objects.get(link_slug="w21704a10")
    print(get_value(operation, "op_id"))
    print(get_value(operation, "job_id__quantity"))      
    print(get_value(operation, "job_id__worker"))    
    print(get_value(operation, "job_id__operat_id__notexist"))  

def get_verbose2(model, field_id, app='core'):
    try:
        if type(model) == str:
            return apps.get_model(app, model)._meta.get_field(field_id).verbose_name
            # Add recursive support
        elif type(model) == ModelBase:
            return model._meta.get_field(field_id).verbose_name
    except:
        return "views.get_verbose error"        

#eg get_verbose(Worker, "job_id__quantity")
def get_verbose(model, field_str, app='core'):
    try:
        if "__" in field_str:
            parent_str, field_str = field_str.split("__", 1)
            print(parent_str, field_str)
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
            #parent = job_id, field = "quantity"
            parentObj = getattr(object, parent_str.replace("_id", ""))
            return get_value(parentObj, field_str)
        else:
            return getattr(object, field_str)
    except AttributeError:
        return "-"

def attempt4():
    print(get_verbose(Operation, "op_id"))
    print(get_verbose(Operation, "job_id__quantity"))

def attempt5():
    job = Job.objects.get(link_slug="w21704")
    print(job.operations)
    


print(CCtoString("AlexB"))
    
    
    
    