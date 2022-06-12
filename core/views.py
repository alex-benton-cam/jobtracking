from ast import operator
from logging import exception
import string
from time import sleep
from django.http import HttpResponseRedirect, QueryDict, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django import forms
from django.db.models import ForeignKey

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, AnonymousUser

from django.contrib import messages
from django.urls import reverse
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from numpy import disp, int64, float64
from requests import request, session
from django.conf import settings

from bootstrap_tracking.settings import DEBUG

from .models import *
import pandas as pd
from core.utils import *
from json import dumps, loads

import re
import os
from io import BytesIO as IO
from django.utils.safestring import mark_safe
from numpy.random import choice

# Alter import data for display and demo purposes
DEMONSTRATE = False

def call_manager():
    pass

def detail_view_exists(request, model, **kwargs):
    modelName = model.__name__
    try:
        slug = kwargs["link_slug"]
        try:
            object = model.objects.get(link_slug=slug)
            return object

        except ObjectDoesNotExist:
            messages.error(request, "{} {} does not exist".format(modelName, slug))
            return redirect("{}s".format(modelName.lower()))

    except:
        messages.error(request, "Failed to get operation ID from url")
        return redirect("{}s".format(modelName.lower()))

"""
# Try to find operation with op_id = "W/10000/A020"
try: 
    operation = Operation.objects.get(op_id="W/10000/A020")

# If operation does not exist
except ObjectDoesNotExist:
    
    # Create error message
    messages.error(request, "Operation does not exist")
    
    # Redirect user to page where alert should be displayed
    return redirect("operations")"""




def render_wrapper(request, template, context={}):
    helplocs = None
    if not isinstance(request.user, AnonymousUser):
        if request.user.last_name:
            context["manager_locations"] = request.user.last_name
        context["user"] = CCtoString(request.user.username)
        if request.user.last_name:
            locs = json.loads(request.user.last_name)
            helplocs = [l for l in locs if Location.objects.get(
                loc_id=l).help_req]

    context["help"] = helplocs if helplocs else None
    return render(request, template, context)


class LoginReq(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = ''


class Index(View):
    template = "_index.html"

    def get(self, request):
        return render_wrapper(request, self.template, {"landing":True})


class Logout(LoginReq):
    template = "_index.html"
    
    def get(self, request):
        un = CCtoString(request.user.username)
        logout(request)
        messages.success(request, "{} successfully logged out".format(un))
        return render_wrapper(request, self.template, {"landing":True})


class UploadLocs(View):

    template = "upload.html"

    def get(self, request):
        return render_wrapper(request, self.template)

    def post(self, request):
        return redirect("locations")

        if "create_workers_button" in request.POST:

            csv_file = request.FILES["csv_file"]

            if not csv_file.name.endswith(".csv"):
                messages.warning(request, "A .csv file must be uploaded")
                return HttpResponseRedirect(reverse("upload"))

            def import_loc(row, model=Operation, dateCols=[], modelDict={}):

                rowDict = row.to_dict()
                obj = Location(**rowDict)
                obj.save()

            loadDF = pd.read_csv(csv_file)
            loadDF = loadDF.where(pd.notnull(loadDF), None)
            loadDF.index.rename("upload_id", inplace=True)
            loadDF.apply(import_loc, axis=1)

            return redirect("locations")

class GenericView(View):
    template = "generic_template.html"
    button_name = "confirm_button"
    
    def do_logic():
        pass
    
    # Function called during a GET request
    def get(self, request):
        
        # Create context variables with which to fill the page
        context = {"page_title": "Example Page Title",
                   "button_name": self.button_name}
        
        # Render the web page
        return render(request, self.template, context)
    
    # Function called during a POST request
    def post(self, request):
        
        # If cofirmation button has been pressed
        if self.button_name in request.POST:
            
            # Do necessary logic
            self.do_logic()
            
            # Redirect user to the same web page            
            return redirect("generic")        
        



class MgSetup(LoginReq):
    template = "mg_setup.html"
    models = [Location, Worker, ScrapCode, FieldDict]

    def import_row(self, row, mod, request):

        try:
            rowDict = row.to_dict()
            obj = mod(**rowDict)
            obj.save()
            return False
        except Exception as e:
            messages.error(
                request, "Upload failed at row <{}> - -  Error message: <{}>".format(str(list(row)), str(e)))
            return True

    def get(self, request):

        context = []

        for model in self.models:
            contextDict = {
                "name": model.__name__,
                "friendly": CCtoString(model.__name__),
                "lower": CCtoString(model.__name__).lower(),
                "example_fp": "{}assets/{}_example.csv".format(settings.STATIC_URL, model.__name__.lower()).lstrip("/"),
                "count": model.objects.count(),
            }
            contextDict["friendly"] = "Datatable Configuration" if model == FieldDict else contextDict["friendly"]
            context.append(contextDict)

        return render_wrapper(request, self.template, {"context": context})

    def post(self, request):

        try:
            type = [p for p in ["download", "upload",
                                "example"] if p in request.POST][0]
            model = [m for m in self.models if m.__name__ in request.POST[type]][0]

            if type == "example":

                path = os.path.join(settings.BASE_DIR,
                                    request.POST["filepath"])
                try:

                    with open(path, 'rb') as fh:
                        response = HttpResponse(
                            fh.read(), content_type="text/csv", charset="utf-8")
                        response['Content-Disposition'] = 'attachment; filename=' + \
                            os.path.basename(path)
                        return response
                except:
                    messages.error(request, "Error in accessing file")
                    return redirect("mgsetup")

            elif type == "download":
                qs = model.objects.all()
                displayFields = [f.name for f in model._meta.get_fields()
                                 if hasattr(model._meta.get_field(f.name), "verbose_name")
                                 and getattr(model._meta.get_field(f.name), "editable", True)
                                 and not isinstance(model._meta.get_field(f.name), ForeignKey)]

                queryData = list(qs.values(*displayFields))
                queryDataDF = pd.DataFrame(queryData)
                csv_file = IO()
                queryDataDF.to_csv(csv_file, index=False)

                print(csv_file)
                response = HttpResponse(
                    csv_file.getvalue(), content_type="text/csv", charset="utf-8")
                response['Content-Disposition'] = 'attachment; filename=existing_{}_data.csv'.format(
                    model.__name__)
                return response

            elif type == "upload":

                try:
                    csv_file = request.FILES["csv_file"]

                    if not csv_file.name.endswith(".csv"):
                        messages.warning(
                            request, "A .csv file must be uploaded")
                        return redirect("mgsetup")

                    loadDF = pd.read_csv(csv_file, index_col=False)
                    loadDF = loadDF.where(pd.notnull(loadDF), None)
                    #loadDF.index.rename("upload_id", inplace=True)
                    errors = loadDF.apply(
                        self.import_row, axis=1, args=(model, request))

                    if True not in list(errors):
                        messages.success(request, "Successful Upload")

                    if model == Location:
                        try:
                            for id in (Location.START, Location.END, Location.INTERIM):
                                rowDict = {"loc_id": id,
                                           "name": id, "many_jobs": True}
                                loc = Location(**rowDict)
                                loc.save()
                        except Exception as e:
                            messages.error(
                                request, "Could not add 'unreleased' and 'finished' locations " + str(e))

                    return redirect("mgsetup")

                except Exception as e:

                    messages.error(
                        request, "Upload of {} failed: {}".format(model.__name__, e))

        except Exception as e:

            messages.error(request, "Invalid post request {}".format(e))
            return redirect("mgsetup")

        return redirect("mgsetup")


class UploadOps(LoginReq):
    template = "mg_upload.html"

    def import_op(self, row, dateCols=[]):
        rowDict = row.to_dict()
        for col in dateCols:
            rowDict[col] = stdDateTime(rowDict[col]) if rowDict[col] else None

        jobFields = ["work_no", "company", "job_name", "quantity"]

        try:
            # Get job object
            parentJob = Job.objects.get(work_no=rowDict["work_no"])

        except ObjectDoesNotExist:
            # Create Job object if not already existing

            if DEMONSTRATE:
                rowDict["company"] = choice(["Manestical Energy Co", "Doover Industrial Systems", "Golden Triad Technology",
                                             "Maleo Manufacturing", "Zeus Produce Industries", "Manufacturing Corner", "Meteorite Manufacturers"])
                rowDict["job_name"] = choice(["Landing Gear", "Instrument Panel", "Propeller", "Suspension Wishbone", "Turbine Blade", "Leafspring", "Engine Manifold", "Nosecone", "Undercarriage Chassis",
                                              "Exhaust Kit", "Drying Rack", "Elevon", "Antenna Mount"])

            jobDict = {key: rowDict[key] for key in jobFields}
            parentJob = Job(**jobDict)
            parentJob.status = Job.PENDING
            parentJob.save()
            parentJob.add_entry("Job uploaded to Shoestring Job Tracking")

            for i, n in enumerate([0, 999]):

                opDict = {"job": parentJob,
                          "op_no": n,
                          "name": (Location.START, Location.END)[i],
                          "active": (True, False)[i],
                          "display": False,
                          "status": (Operation.ACTIVE, Operation.PENDING)[i],
                          "issue_no": rowDict["issue_no"],
                          "location": Location.objects.get(loc_id=(Location.START, Location.END)[i])}

                obj = Operation(**opDict)
                obj.save()

                if i == 0:
                    obj.check_in(Location.objects.get(loc_id=(Location.START)))

        finally:
            # Change op dict to reflect job creation
            rowDict["job"] = parentJob

            for field in jobFields:
                rowDict.pop(field, None)

        
                                       
        
        if rowDict["worker"]:
            try:
                parentWorker = Worker.objects.get(name=rowDict["worker"])
                rowDict["worker"] = parentWorker
            except ObjectDoesNotExist:
                messages.warning(
                    self.request, "Worker '" +
                    rowDict["worker"] + "' does not Exist"
                )
                rowDict["worker"] = None
        elif DEMONSTRATE:
            rowDict["worker"] = choice(['Hina Norton', 'Cai Adam', 'Eden Moore', 'Irfan Morgan', 'Akeem Wicks', 'Yasmeen Chapman', 'Effie Simons', 'Tyrone Wheatley', 'Ralph Peters', 'Krisha James', 'Alex Benton', 'Tim Minshall', 'Greg Hawkridge'])
            

        if rowDict["location"]:
            try:
                parentLocation = Location.objects.get(name=rowDict["location"])
                rowDict["location"] = parentLocation
                if DEMONSTRATE and choice([True, True, False]):
                    rowDict["insp_bool"] = not parentLocation.many_jobs

            except ObjectDoesNotExist:
                try:
                    parentLocation = Location.objects.get(
                        loc_id=rowDict["location"])
                    rowDict["location"] = parentLocation
                except ObjectDoesNotExist:
                    messages.warning(
                        self.request, "Location '" +
                        rowDict["location"] + "' does not Exist"
                    )
                    rowDict["location"] = None

        obj = Operation(**rowDict)
        # obj.save()
        obj.phase = Operation.PENDING if obj.insp_bool else Operation.NONE
        obj.save()

        if obj.insp_bool:
            create_interim_op(obj)

    def download_data(self, data, filename):

        queryDataDF = pd.DataFrame(data)
        csv_file = IO()
        queryDataDF.to_csv(csv_file, index=False)

        print(csv_file)
        response = HttpResponse(
            csv_file.getvalue(), content_type="text/csv", charset="utf-8")
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
            filename)
        return response

    def get(self, request):
        
        # Select a list of objects for display in the table
        qs = Job.objects.filter(status=Job.COMPLETE)
        
        # Load a fieldDict (table config) using the config's ID
        fieldDict = FieldDict.objects.get(id="upload_ops_complete_jobs").get()
        
        # Use the get_datatable utility to create displayable data
        fieldDict, data = get_datatable(fieldDict, qs, Job)

        # Make a context variable containing the fieldDict and data
        context = {"fieldDict": fieldDict, "data": data}

        # Render the web page
        return render_wrapper(request, self.template, context)

    def post(self, request):

        dbprint(request.POST)
        post = request.POST
        # return redirect("upload")
        if "upload_operations" in post:

            csv_file = request.FILES["csv_file"]

            if not csv_file.name.endswith(".csv"):
                messages.warning(request, "A .csv file must be uploaded")
                return HttpResponseRedirect(reverse("upload"))

            def stripCol(col):
                return col
                try: 
                    return col.str.strip()
                except:
                    return col

            loadDF = pd.read_csv(csv_file)
            loadDF = loadDF.where(pd.notnull(loadDF), None)
            loadDF.index.rename("upload_id", inplace=True)
            loadDF.apply(stripCol, axis=0)
            loadDF.apply(self.import_op, axis=1, dateCols=[
                "start_time", "end_time"])

            return redirect("operations")

        elif "download_completed_jobs" in post:
            qs = Job.objects.filter(status=Job.COMPLETE)
            displayFields = [
                f.name for f in Job._meta.get_fields() if f.name != "operation"]
            entryFields = [f.name for f in Entry._meta.get_fields()]
            
            
            displayFields = ["work_no", "num_scrap", "quantity", "company", "job_name", "status"]
            dbprint(displayFields)
                        
            queryData = list(qs.values(*displayFields))
            dbprint(queryData)
            for jobDict in queryData:
                job = Job.objects.get(work_no=jobDict["work_no"])
                jobDict["job_log"] = str(dumps(list(job.entry_set.all().values(
                    *entryFields)), indent=4, sort_keys=True, default=str))

            name = "Completed Jobs {}".format(
                displayDT(datetime.now()).replace("/", "-", -1).replace(":", "-"))
            return self.download_data(queryData, name)

        elif "delete_completed_jobs" in post:
            modalDict = {
                "name": "confirm_delete_completed_jobs",
                "message": "Confirm deletion of all completed jobs and all associated operations and job logs. This will reduce the amount of data on the system, potentially improving performance.",
                "title": "Confirm Deletion",
                "action": "Deleted Completed Jobs",
                "message_bottom": "However, it is strongly reccomended that completed jobs be downloaded first - this action cannot be undone."}
            create_confirm_modal(request, **modalDict)
            return redirect("upload")

        elif "download_completed_operations" in post:
            qs = Operation.objects.filter(status=Operation.COMPLETE)
            displayFields = [f.name for f in Operation._meta.get_fields()]
            displayFields.remove("entry")
            entryFields = [f.name for f in Entry._meta.get_fields()]

            queryData = list(qs.values(*displayFields))
            for opDict in queryData:
                op = Operation.objects.get(op_id=opDict["op_id"])
                opDict["operation_log"] = dumps(list(op.entry_set.all().values(
                    *entryFields)), indent=4, sort_keys=True, default=str)
                print()

            name = "Completed Operations {}".format(
                displayDT(datetime.now()).replace("/", "-", -1).replace(":", "-"))
            return self.download_data(queryData, name)

        elif "download_completed_job_logs" in post:
            qs = Operation.objects.filter(status=Operation.COMPLETE)
            displayFields = [f.name for f in Entry._meta.get_fields()]

            entryData = []
            for job in qs:
                entries = job.entry_set.all()
                entryData += list(entries.values(*displayFields))

            name = "Job Logs of Completed Operations {}".format(
                displayDT(datetime.now()).replace("/", "-", -1).replace(":", "-"))
            return self.download_data(entryData, name)

        elif "download_example_ops" in post:
            path = os.path.join(settings.BASE_DIR, "static/assets/operation_example.csv")
            
            with open(path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="text/csv", charset="utf-8")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(path)
                return response

        elif "confirm_delete_completed_jobs" in post:
            Job.objects.filter(status=Job.COMPLETE).delete()
            messages.success(
                request, "All completed jobs have now been deleted")
            

        else:
            messages.error(request, "Invalid opst request {}".format(post))
        return redirect("upload")


class ModelView(View):

    model = None
    template = "mg_datatable.html"

    def get(self, request):

        query = None

        if self.model == Operation:
            query = Operation.objects.filter(display=True)
            pageTitle = "All Operations"
            fieldDict = FieldDict.objects.get(id="all_operations_table").get()

        elif self.model == Job:
            pageTitle = "All Jobs"
            fieldDict = FieldDict.objects.get(id="all_jobs_table").get()

        elif self.model == Worker:
            #all_workers_table
            pageTitle = "All Operators"
            fieldDict = FieldDict.objects.get(id="all_workers_table").get()
            
        elif self.model == Location:
            #all_locations_table
            pageTitle = "All Locations"
            fieldDict = FieldDict.objects.get(id="all_locations_table").get()

        else:
            displayFields = [f.name for f in self.model._meta.get_fields()
                             if hasattr(self.model._meta.get_field(f.name), "verbose_name")
                             and f.name != "link_slug"]
            fieldDict = {k: {} for k in displayFields}

        query = query if query is not None else self.model.objects.all()

        fieldDict, queryData = get_datatable(fieldDict, query, self.model)
        context = {"fieldDict": fieldDict,
                   "queryData": queryData,
                   "page_title": pageTitle}

        return render_wrapper(request, self.template, context)

"""
class OpDetail(View):

    template = "op_operation.html"
    model = Operation

    def template_args(self, link):

        operation = Operation.objects.get(link_slug=link)

        fieldDict = {
            # "op_id": {"verbose": "Operation", "href": "abs_link"},
            "job_id__work_no": {"verbose": "Job", "href": "job_id__abs_link"},
            "job_id__job_name": {},
            "job_id__company": {},
            "phase": {},
            "insp_bool": {},
            "part_no": {},
            "job_id__quantity": {},
            "drg_no": {},
            "location_id__name": {"verbose": "Location", "href": "location_id__abs_link"},
            "start_time": {},
            "end_time": {},
            "planned_set": {},
            "planned_run": {},
        }

        linkFields = [v.get("href")
                      for v in fieldDict.values() if v.get("href")]
        opData = {f: get_value(operation, f)
                  for f in list(fieldDict.keys()) + linkFields}

        for field_str in fieldDict.keys():
            if "verbose" not in fieldDict[field_str]:
                fieldDict[field_str]["verbose"] = get_verbose(
                    self.model, field_str)

        scrapCodes = {s.id: s.name for s in ScrapCode.objects.all()}

        return {"fieldDict": fieldDict,
                "opData": dict(opData),
                "jobLog": get_job_log(operation.job),
                "scrapCodes": scrapCodes,
                }

    def get(self, request, *args, **kwargs):
        operation = Operation.objects.get(link_slug=kwargs["link_slug"])
        context = self.template_args(operation.link_slug)
        return render_wrapper(request, self.template, context)

    def post(self, request):
        messages.info(request, "POST not implemented")
        return redirect("operations")
"""

class JobDetail(View):
    template = "mg_job.html"

    def get(self, request, *args, **kwargs):

        result = detail_view_exists(request, Job, **kwargs)
        if not isinstance(result, Job):
            return result
        else:

            job = Job.objects.get(link_slug=kwargs["link_slug"])
            job.save()
            fieldDict = FieldDict.objects.get(id="job_detail_main").get()

            operation = str(job.operation)

            linkFields = [v.get("href")
                          for v in fieldDict.values() if v.get("href")]
            jobData = {f: get_value(job, f)
                       for f in list(fieldDict.keys()) + linkFields}

            for field_str in fieldDict.keys():
                if "verbose" not in fieldDict[field_str]:
                    fieldDict[field_str]["verbose"] = get_verbose(
                        job, field_str)

            opFieldDict = FieldDict.objects.get(id="job_detail_ops").get()

            opQuery = job.operation_set.all()
            opFieldDict, opData = get_datatable(
                opFieldDict, opQuery, Operation)

            context = {"operation": operation,
                       "fieldDict": fieldDict,
                       "jobData": jobData,
                       "jobLog": get_job_log(job),
                       "opFieldDict": opFieldDict,
                       "opData": opData}

            dbprint(jobData)

            return render_wrapper(request, self.template, context)


class LocDetail(View):
    template = "_location.html"

    def get(self, request, *args, **kwargs):

        result = detail_view_exists(request, Location, **kwargs)
        if not isinstance(result, Location):
            return result
        else:
            location = result

        query = location.operation_set.all()
        fieldDict = FieldDict.objects.get(id="location_detail_main").get()
        fieldDict, data = get_datatable(fieldDict, query, Operation)
        
        context = {"location": location.link_slug,
                   "fieldDict": fieldDict,
                   "data": data,
                   "locName": location.name}

        return render_wrapper(request, self.template, context)


class WorkerDetail(LoginReq):
    template = "_worker.html"

    def get(self, request, *args, **kwargs):

        result = detail_view_exists(request, Worker, **kwargs)
        if not isinstance(result, Worker):
            return result
        else:
            worker = result

        query = worker.operation_set.all()
        fieldDict = FieldDict.objects.get(id="worker_detail_main").get()
        fieldDict, data = get_datatable(fieldDict, query, Operation)
        context = {"location": worker.link_slug,
                   "fieldDict": fieldDict,
                   "data": data,
                   "name": worker.name}

        return render_wrapper(request, self.template, context)
"""
class ExampleDisplay(View):
    template = "_example.html"

    def get(self, request, *args, **kwargs):

        query = Operation.objects.all()        
        fieldDict = FieldDict.objects.get(id="op_dash_tab_2").get()        
        fieldDict, data = get_datatable(fieldDict, query, Operation)        
        context = {"fieldDict": fieldDict,
                   "data": data}

        return render_wrapper(request, self.template, context)
    
    def post(self, request):
        if "advance_modal" in post:
            # Check operation out"""
            




class Op_OperationDash(View):

    template = "op_operation.html"
    model = Operation
    confirm_modal = "operation_confirm_modal"

    def template_args(self, link):

        operation = Operation.objects.get(link_slug=link)

        fieldDict1 = FieldDict.objects.get(id="op_dash_tab_1").get()
        fieldDict2 = FieldDict.objects.get(id="op_dash_tab_2").get()

        if operation.insp_bool:
            extra = FieldDict.objects.get(id="op_dash_tab_2_extra").get()
            fieldDict2 = {**fieldDict2, **extra}

        fieldDict1, opData1 = get_singletable(fieldDict1, operation, Operation)
        fieldDict2, opData2 = get_singletable(fieldDict2, operation, Operation)
        scrapCodes = {s.id: s.name for s in ScrapCode.objects.all()}

        return {"fieldDict1": fieldDict1,
                "opData1": dict(opData1),
                "fieldDict2": fieldDict2,
                "opData2": dict(opData2),
                "jobLog": get_job_log(operation.job),
                "scrapCodes": scrapCodes,
                }

    def get(self, request, *args, **kwargs):

        try:
            operation = Operation.objects.get(link_slug=kwargs["link_slug"])
            manager = True
        except:
            manager = False

        try:

            if manager:
                location = operation.location
            else:
                location = Location.objects.get(
                    loc_id=request.session['location_id'])

            try:
                if not manager:
                    operation = location.operation_set.get(
                        status=Operation.ACTIVE)

                try:
                    phaseNo = Operation.PHASE_LIST.index(operation.phase)
                    nextPhase = Operation.PHASE_LIST[phaseNo+1]
                except:
                    phaseNo = None
                    nextPhase = None

                nameDict = {Operation.NONE: "Complete Operation",
                            Operation.PENDING: "Start Setup Phase",
                            Operation.SETUP: "Start One-Off Phase",
                            Operation.ONEOFF: "Send to Interim Inspection",
                            Operation.INTERIM: "Start Full Batch Phase",
                            Operation.FULLBATCH: "Complete Operation",
                            Operation.COMPLETE: "Operation already Complete"
                            }

                # Gets data tables, job log, and scrap code
                context = self.template_args(operation.link_slug)
                # Add simple arguments
                context["submit"] = "get"
                context["op_id"] = operation.op_id
                context["op_name"] = operation.name
                context["loc_id"] = location.loc_id
                context["loc_name"] = location.name
                context["job_title"] = str(operation.job)
                context["manager"] = manager
                context["phase"] = operation.phase
                context["next_phase"] = nextPhase
                context["op_status"] = operation.status
                context["button_text"] = nameDict[operation.phase]

                return render_wrapper(request, self.template, context)

                # print(request.session["current_operation"])
                #operation = Operation.objects.get(op_id=request.session["current_operation"])

            except MultipleObjectsReturned:
                messages.warning(
                    request, "More than one operation active on this location")
                return redirect("machine")

            except:
                messages.warning(
                    request, "An operation must be checked in to first")
                return redirect("machine")

        except:
            
            messages.warning(request, "No machine active on device")
            return redirect("factory")

    def post(self, request, *args, **kwargs):
        post = request.POST

        try:
            location = Location.objects.get(loc_id=post["loc_id"])
        except Exception as e:
            messages.error(request, "Can't Retrieve location " + str(e))
            return redirect("operation")
            
        try:
            operation = Operation.objects.get(op_id=post["op_id"])
            job = operation.job
        except Exception as e:
            messages.error(request, "Can't Retrieve operation " + str(e))
            return redirect("operation")

        if "advance_to_next_button" in post:

            if operation.phase is not None:

                if operation.phase != Operation.COMPLETE:

                    phaseNo = Operation.PHASE_LIST.index(operation.phase)
                    nextPhase = Operation.PHASE_LIST[phaseNo+1]
                    action = "Confirm"
                    message_bottom = None
                    name = "advance_modal"

                    if operation.phase == Operation.PENDING:
                        title = "Begin Setup"
                        message = "Confirm Setup of operation {} has begun".format(
                            operation.op_id)

                    elif operation.phase == Operation.ONEOFF:
                        title = "Move to Interim Inspection"
                        message = "Confirm first off of operation {} is complete and is being moved to interim inspection".format(
                            operation.op_id)

                    elif operation.phase == Operation.INTERIM:
                        title = "Interim Inspection Completed"
                        message = "Confirm interim inspection of operation {} is complete".format(
                            operation.op_id)
                        message_bottom = "Did interim inspection pass or fail?"
                        action = "PASS"
                        action2 = "FAIL"
                        name = "inspection_modal"

                    elif operation.phase == Operation.FULLBATCH:
                        title = "Operation Complete"
                        message = "Confirm operation {} is complete".format(
                            operation.op_id)

                    else:
                        title = "Advance Operation to Next Phase"
                        message = "Confirm phase '{}' of operation {} is complete and advance to '{}'".format(
                            operation.phase, operation.op_id, nextPhase)
                        action = "Advance to {}".format(nextPhase)

                    modalDict = {
                        "name": name,
                        "message": message,
                        "title": title,
                        "data": {"next_phase": nextPhase,
                                 "curr_phase": operation.phase,
                                 "op_id": operation.op_id,
                                 "loc_id": location.loc_id},
                        "action": action,
                        "message_bottom": message_bottom}

                    try:
                        modalDict["action2"] = action2
                    except:
                        pass

                    create_confirm_modal(request, **modalDict)
                    return redirect("operation")

                # phase = "Complete"
                else:
                    messages.error(
                        request, "Should not be able to advance a complete job")

            # Operation does not have interim inspection
            else:

                modalDict = {
                    "name": "advance_modal",
                    "message": "Confirm operation {} is complete".format(operation.op_id),
                    "title": "Operation Complete",
                    "data": {"next_phase": Operation.COMPLETE,
                             "curr_phase": operation.phase,
                             "op_id": operation.op_id,
                             "loc_id": location.loc_id},
                    "action": "Confirm", }

                create_confirm_modal(request, **modalDict)
                return redirect("operation")

            job.add_entry("Query Submitted " + str(operation))
            return redirect("operation")

        elif "undo_last_button" in post:
            latest = job.entry_set.latest("dt")
            latest.undone = True
            latest.save()
            return redirect("operation")

        elif "report_scrap_button" in post:
            try:
                assert(int(post["quantity"]) > 0)
            except:
                messages.warning(
                    request, "Must give a valid scrap quantity greater than 1")
                return redirect("operation")

            data = dumps({"scrapCode": post["scrapCode"],
                          "quantity": post["quantity"],
                          "loc_id": post["loc_id"],
                          "op_id": post["op_id"]})
            operation.add_entry("{} scrap reported ({})".format(post["quantity"], post["scrapCode"]),
                                data=data)
            operation.save()
            return redirect("operation")


        
        # If the button named 'call_manager_button' is pressed
        elif "call_manager_button" in request.POST:
            
            # Specify the popup's content
            modalDict = {
                "title": "Confirm Help Required",
                "name": "call_manager_modal",
                "message": "Call manager or cancel help request",
                "action": "Confirm",
                "action2": "Cancel",
                "do_ws": "true",
            }

            # Call modal creation function
            create_confirm_modal(request, **modalDict)
            
            # Redirect user to the appropriate page
            return redirect("operation")

        # If the button corresponding to 'action' is pressed
        elif "call_manager_modal" in request.POST:
            
            # Call manager
            call_manager()
            
            

        elif "advance_modal" in post:
            
            try:
                next = post["next_phase"]
            except:
                messages.error(request, "No 'next_phase' value passed")
                return redirect("operation")

            message = "{} phase begun".format(post["next_phase"])
            if next == Operation.SETUP:
                operation.actual_start_time = stdDateTime()

            elif next == Operation.ONEOFF:
                operation.actual_set = minutesSince(operation.last_action_time)

            elif next == Operation.INTERIM:
                operation.actual_oneoff = minutesSince(
                    operation.last_action_time)

                insp_op = Operation.objects.get(op_id=operation.op_id+"I")
                insp_op.status = Operation.PENDING
                insp_op.save()

            elif next == Operation.FULLBATCH:
                operation.location = location
                operation.actual_insp = minutesSince(
                    operation.last_action_time)

            elif next == Operation.COMPLETE:

                if operation.insp_bool:
                    operation.actual_fullbatch = minutesSince(
                        operation.last_action_time)
                    operation.actual_run = round(
                        operation.actual_fullbatch + operation.actual_oneoff, 2)
                else:
                    operation.actual_run = minutesSince(
                        operation.last_action_time)

                operation.check_out()
                operation.phase = Operation.COMPLETE
                operation.save()
                messages.success(
                    request, "Operation {} completed".format(post["op_id"]))
                return redirect("machine")

            else:
                messages.error(
                    request, "Wrong value for next phase: {}".format(next))
                return redirect("operation")

            messages.success(request, message)
            operation.last_action_time = stdDateTime()
            operation.phase = post["next_phase"]
            operation.save()
            operation.add_entry("{} phase begun".format(operation.phase))
            return redirect("operation")

        elif "inspection_modal" in post:
            res = post["inspection_modal"]

            if res == "FAIL":
                messages.success(
                    request, "Inspection failed, returning to One-Off phase")
                operation.phase = Operation.ONEOFF
                operation.add_entry("Insp. failed, one-off restarted")

            elif res == "PASS":
                messages.success(
                    request, "Inspection passed, moving to Full Batch phase")
                operation.phase = Operation.FULLBATCH
                operation.add_entry("Insp. passed, full batch started")

            else:
                messages.error(request, "Invalid inspection modal result {}".format(
                    post["inspection_modal"]))

            operation.actual_insp = minutesSince(operation.last_action_time)
            operation.last_action_time = stdDateTime()
            operation.save()
            return redirect("operation")

        else:
            messages.error(request, "Invalid post request: " + str(post))
            return redirect("operation")


class Op_MachineView(View):

    template = None
    location = None
    confirm_modal = "machine_confirm_modal"
    buffer_modal = "confirm_buffer_modal"

    def machine_check_in(self, request, op, loc, many_jobs=False):

        message = "Operation '{}' checked in at '{}.'".format(
            op.op_id, loc.name)
        messages.success(request, message)
        op.check_in(loc)

        if many_jobs:
            return redirect("machine")
        else:
            return redirect("operation")

    def machine_check_out(self, request, op, loc, many_jobs=False):
        if many_jobs == False:
            messages.error(
                request, "Should not call machine_check_out from a non-buffer")

        message = "Operation '{}' checked out from '{}.'".format(
            op.op_id, loc.name)
        messages.info(request, message)
        op.check_out()
        return redirect("machine")

    def get(self, request, *args, **kwargs):

        try:
            location = request.session["location_id"]
            location = Location.objects.get(loc_id=location)
        except:
            messages.warning(
                request, "A location must be selected to check in to a job")
            return redirect("factory")
        
        queryPending = location.operation_set.all().filter(status=Operation.PENDING)
        if location.loc_id == Location.INTERIM:
            for op in queryPending:
                try:
                    paired = Operation.objects.get(op_id=op.op_id[:-1])
                    if paired.phase != Operation.INTERIM:
                        queryPending = queryPending.exclude(op_id=op.op_id)
                except:
                    pass

            
        queryActive = location.operation_set.all().filter(status=Operation.ACTIVE)
        queryComplete = location.operation_set.all().filter(status=Operation.COMPLETE)

        fieldDict = FieldDict.objects.get(id="machine_dash").get()

        pendFieldDict, pendData = get_datatable(
            fieldDict, queryPending, Operation)

        if queryActive:
            actFieldDict, actData = get_datatable(
                fieldDict, queryActive, Operation)
        else:
            actFieldDict, actData = (None, None)

        # fieldDict.pop("op_id")
        compFieldDict, compData = get_datatable(
            fieldDict, queryComplete, Operation)

        context = {"pendFieldDict": pendFieldDict,
                   "pendData": pendData,
                   "actFieldDict": actFieldDict,
                   "actData": actData,
                   "compFieldDict": compFieldDict,
                   "compData": compData,
                   "locName": location.name,
                   "loc_id": location.loc_id,
                   }

        if location.many_jobs:
            self.template = "op_buffer.html"
            if "last_action" in request.session:
                context["last_action"] = request.session["last_action"]
            else:
                context["last_action"] = "in"

        else:
            self.template = "op_machine.html"

        return render_wrapper(request, self.template, context)

    def post(self, request, *args, **kwargs):

        #validPosts = ["check_in_button", "confirm_skip_modal"]

        if "check_in_button" in request.POST or "add_to_buffer_button" in request.POST:
            buffer_location = True if "add_to_buffer_button" in request.POST else False
            dbprint(request.POST)
            # Try if checked into a location
            try:
                device_location = Location.objects.get(
                    loc_id=request.session["location_id"])

                # If operation ID is valid
                try:
                    operation = Operation.objects.get(
                        op_id=request.POST["operation_id"])

                # Try finding job if work_no provided
                except ObjectDoesNotExist:
                    try:
                        job = Job.objects.get(
                            work_no=request.POST["operation_id"])

                        # Try getting operation from list of pending jobs
                        try:
                            opsatloc = job.operation_set.filter(
                                location=device_location)
                            pendingops = opsatloc.filter(
                                status=Operation.PENDING)
                            operation = pendingops.order_by("op_no")[0]

                        except Exception as e:
                            messages.warning(
                                request, "No pending operations from job {} at current machine. {}".format(request.POST["operation_id"]), e)
                            return redirect("machine")

                    except ObjectDoesNotExist:
                        messages.warning(
                            request, "Invalid operation or job ID: {}".format(request.POST["operation_id"]))
                        return redirect("machine")

                finally:

                    buffer_passed = False
                    if "add_to_buffer_button" in request.POST:

                        if request.POST["add_to_buffer_button"] == "out":
                            request.session["last_action"] = "out"

                            if operation.location == device_location:
                                if operation.status == Operation.ACTIVE:
                                    self.machine_check_out(
                                        request, operation, device_location, many_jobs=True)
                                else:
                                    messages.warning(
                                        request, "Cannot check out a non-active job")
                                    request.session["last_action"] = "in"
                            else:
                                messages.warning(
                                    request, "Cannot check out a job which is not at this machine")

                        elif request.POST["add_to_buffer_button"] == "in":
                            request.session["last_action"] = "in"

                            if operation.location == device_location:
                                if operation.status == Operation.PENDING:
                                    buffer_passed = True
                                    #self.machine_check_in(request, operation, device_location, many_jobs=True)
                                    #messages.info(request, "Succesfully Checked out {}".format(operation.op_id))
                                else:
                                    messages.warning(
                                        request, "Cannot check in a non-pending job")
                                    request.session["last_action"] = "out"
                            else:
                                messages.warning(
                                    request, "Cannot check in a job which is not at this machine")

                        else:
                            messages.error(
                                request, "Wrong value for add_to_buffer_button {}".format(str(request.POST)))

                        if not buffer_passed:
                            return redirect("machine")

                    active_ops = device_location.operation_set.filter(
                        status=Operation.ACTIVE)

                    # Exclude single-job machines with active ops
                    if not (active_ops and not device_location.many_jobs):

                        # If trying to check into a completed job
                        if operation.status != Operation.COMPLETE:

                            skippedOps = operation.job.operation_set.filter(
                                status=Operation.PENDING, op_no__lt=operation.op_no)
                            wrongLoc = False if operation.location == device_location else True

                            # Change name of modal based on adding to buffer or machine
                            modalName = self.buffer_modal if device_location.many_jobs else self.confirm_modal
                            try:
                                activeop = operation.job.operation_set.get(
                                    status=Operation.ACTIVE)
                                activeopmessage = "(operation {} is currently active at {})".format(
                                    activeop, activeop.location)
                            except:
                                activeopmessage = ""

                            # Planned next operation Checked in to planned location
                            if not skippedOps and not wrongLoc:
                                return self.machine_check_in(request, operation, device_location, many_jobs=device_location.many_jobs)

                            # Check in will skip operations and set operation to a different machine
                            elif skippedOps and wrongLoc:
                                message = "By checking in operation {}, you will mark the following operations as complete {}".format(
                                    operation.op_id, activeopmessage)
                                message_bottom = "The operation is also planned for a different location: {}".format(
                                    operation.location)
                                table = [[o.op_id, o.location.name, o.name]
                                         for o in skippedOps]
                                modalDict = {
                                    "name": modalName,
                                    "message": message,
                                    "message_bottom": message_bottom,
                                    "table": table,
                                    "title": "Check in will skip operations and set operation to a different machine",
                                    "data": {"op_id": operation.op_id,
                                             "location": device_location.loc_id},
                                    "action": "Confirm check in at {} and skip {} ops".format(device_location.name, len(skippedOps))
                                }
                                create_confirm_modal(request, **modalDict)
                                return redirect("machine")

                            # Check in will set operation to a different machine
                            elif not skippedOps and wrongLoc:
                                message = "Operation {} is allocated to: {}".format(
                                    str(operation), operation.location.name,)

                                modalDict = {
                                    "name": modalName,
                                    "message": message,
                                    "title": "Check in will set operation to a different machine",
                                    "data": {"op_id": operation.op_id,
                                             "location": device_location.loc_id},
                                    "action": "Confirm check in at {}".format(device_location.name)
                                }
                                create_confirm_modal(request, **modalDict)
                                return redirect("machine")

                            # Check in will skip operations
                            elif skippedOps and not wrongLoc:
                                message = "By checking in operation {}, you will mark the following operations as complete {}".format(
                                    operation.op_id, activeopmessage)
                                table = [[o.op_id, o.location.loc_id, o.name]
                                         for o in skippedOps]
                                modalDict = {
                                    "name": modalName,
                                    "message": message,
                                    "table": table,
                                    "title": "Check in will skip operations",
                                    "data": {"op_id": operation.op_id,
                                             "location": device_location.loc_id},
                                    "action": "Confirm Skip {} Operation{}".format(len(skippedOps), "s" if len(skippedOps) > 1 else "")
                                }
                                create_confirm_modal(request, **modalDict)
                                return redirect("machine")

                        else:
                            messages.warning(request,
                                             "Cannot check in to an already completed operation")
                            return redirect("machine")
                    else:
                        messages.warning(request,
                                         "There is already a job active at {}: {}.".format(device_location.name, device_location.operation_set.all()[0].op_id))

                        return redirect("operation")

            except ObjectDoesNotExist:
                messages.warning(
                    request, "Location should be set before checking in to a job (this could also be a server error)")
                return redirect("factory")

        elif "add_to_buffer_button" in request.POST:

            # Try if checked into a location
            try:
                device_location = Location.objects.get(
                    loc_id=request.session["location_id"])

                # If operation ID is valid
                try:
                    operation = Operation.objects.get(
                        op_id=request.POST["operation_id"])

                # Try finding job if work_no provided
                except ObjectDoesNotExist:
                    try:
                        job = Job.objects.get(
                            work_no=request.POST["operation_id"])

                        # Try getting operation from list of pending jobs
                        try:
                            opsatloc = job.operation_set.filter(
                                location=device_location)
                            pendingops = opsatloc.filter(
                                status=Operation.PENDING)
                            operation = pendingops.order_by("op_no")[0]

                        except Exception as e:
                            messages.warning(
                                request, "No pending operations from job {} at current machine. {}".format(request.POST["operation_id"]), e)
                            return redirect("machine")

                    except ObjectDoesNotExist:
                        messages.warning(
                            request, "Invalid operation or job ID: {}".format(request.POST["operation_id"]))
                        return redirect("machine")

                finally:

                    if request.POST["add_to_buffer_button"] == "in":
                        pass

                    elif request.POST["add_to_buffer_button"] == "out":
                        pass
                    else:
                        messages.error(
                            request, "Wrong value for add_to_buffer_button {}".format(str(request.POST)))

            except ObjectDoesNotExist:
                messages.warning(
                    request, "Location should be set before checking in to a job")
                return redirect("factory")

        elif self.confirm_modal in request.POST or self.buffer_modal in request.POST:

            operation = Operation.objects.get(op_id=request.POST["op_id"])
            location = Location.objects.get(loc_id=request.POST["location"])

            return self.machine_check_in(request, operation, location, many_jobs=location.many_jobs)

        else:
            print(request.POST)
            messages.error(request, "Invalid post request")
            return redirect("machine")


class Op_FactoryFloor(View):

    template = "op_factory.html"

    def get(self, request, *args, **kwargs):

        query = Location.objects.all()
        fieldDict = {
            "loc_id": {"href": "abs_link"},
            "name": {},
            "worker": {},
        }
        fieldDict, queryData = get_datatable(fieldDict, query, Location)
        context = {"fieldDict": fieldDict,
                   "data": queryData}

        return render_wrapper(request, self.template, context)

    def post(self, request, *args, **kwargs):

        if "select_machine_button" in request.POST:

            try:
                location = Location.objects.get(
                    loc_id=request.POST["machine_id"])
                request.session['location_id'] = location.loc_id

                return redirect("machine")
            except:
                if request.POST["machine_id"].lower() == "clear":
                    request.session['location_id'] = None
                    messages.success(request, "Location Cookie Cleared")
                else:
                    messages.warning(
                        request, "Please enter a valid location ID")
                return redirect("factory")

        else:
            print(request.POST)
            messages.error(request, "Invalid post request")
            return(redirect("factory"))


class Login(View):
    template = 'login.html'

    def get(self, request):
        form = AuthenticationForm()
        return render_wrapper(request, self.template, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Successful Login")
            return redirect("index")
        else:
            messages.warning(request, "Failed to Login")
            return redirect("index")
