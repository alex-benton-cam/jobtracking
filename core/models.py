from django.db import models
from datetime import date, datetime
from core.utils import *
from django.utils.text import slugify
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

class Worker(models.Model):
    name = models.CharField("Name", max_length=40, primary_key=True, unique=True)
    
    # Calculated Fields
    link_slug = models.CharField("Link Slug", max_length=30, unique=True, editable=False)   
    abs_link = models.CharField("Link", max_length=30, unique=True, editable=False)
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.link_slug = slugify(self.name)
        self.abs_link = "/worker/" + self.link_slug
        super(Worker, self).save(*args, **kwargs)

class Location(models.Model):
    # Calculated Fields
    link_slug = models.CharField("Link Slug", max_length=30, unique=True, editable=False)   
    abs_link = models.CharField("Link", max_length=30, unique=True, editable=False)
    
    # Entered Fields
    loc_id = models.CharField("ID", max_length=40, primary_key=True)
    name = models.CharField("Name", max_length=50, unique=True)
    #machine = models.BooleanField("Machine", default=True)
    many_jobs = models.BooleanField("Many Jobs", default=False)
    help_req = models.BooleanField("Help Needed", default=False)
    START = "Unreleased"
    END = "Finished"
    INTERIM = "Interim Insp."
    
    
       
    # Relationships
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Worker")
    
    def __str__(self):
        return self.loc_id
    
    def save(self, *args, **kwargs):
        self.link_slug = slugify(self.loc_id)
        self.abs_link = "/location/" + self.link_slug
        super(Location, self).save(*args, **kwargs)


class Company(models.Model):
    # Calculated Fields
    link_slug = models.CharField("Link Slug", max_length=30, unique=True, editable=False)   
    abs_link = models.CharField("Link", max_length=30, unique=True, editable=False)   

    # Entered Fields
    id = models.CharField("ID", max_length=10, primary_key=True)
    name = models.CharField("Name", max_length=100)
    
    def __str__(self):
        return self.name + " " + self.id
    
    def save(self, *args, **kwargs):
        self.link_slug = slugify(self.id)
        self.abs_link = "/company/" + self.link_slug
        super(Job, self).save(*args, **kwargs)

class Job(models.Model):
    # Calculated Fields
    link_slug = models.CharField("Link Slug", max_length=30, unique=True, editable=False)   
    abs_link = models.CharField("Link", max_length=30, unique=True, editable=False)
    num_scrap = models.IntegerField("Qty Scrapped", null=True, blank=True)
    
    
    # Entered Fields
    work_no = models.CharField("Work No", max_length=50, primary_key=True)
    company = models.CharField("Company", max_length=50)
    job_name = models.CharField("Job Name", max_length=50)
    quantity = models.IntegerField("Qty.")
    #job_log = models.JSONField("Job Log", blank=True, null=True)
        
    # Relationships
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Current Worker")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Current Location")
    
    # Current operation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, editable=False)
    object_id = models.CharField("Operation ID", max_length=30, null=True, editable=False)
    operation = GenericForeignKey()
    
    # Operation Overall Status
    NONE = None
    PENDING = "Pending"
    ACTIVE = "Active"
    COMPLETE = "Complete"
    STATUS_CHOICES = [(PENDING, 'Pending'), (ACTIVE, 'Active'), (COMPLETE, 'Complete'), (NONE, None)]
    status = models.CharField("Job Status", max_length=10, choices=STATUS_CHOICES, default=PENDING, editable=False, blank=True, null=True)
    
    def add_entry(self, msg="Entry Added", **kwargs):   
        dt = datetime.now(tz=pytz.utc).astimezone(TZINFO)  
        newEntry = apps.get_model("core", "Entry").objects.create(message=msg, dt=dt, job=self, **kwargs)
        newEntry.save()
        self.save()
        return newEntry
            
    def __str__(self):
        return self.work_no + " " + self.job_name
    
    def save(self, *args, **kwargs):
        self.link_slug = slugify(self.work_no)
        self.abs_link = "/job/" + self.link_slug         
        
        scrap = 0
        for e in self.entry_set.all():
            if e.data:
                d = json.loads(e.data)
                if "scrapCode" in d:
                    d["quantity"] = 0 if not d["quantity"] else int(d["quantity"])
                    scrap += int(d["quantity"])
        self.num_scrap = scrap
        super(Job, self).save(*args, **kwargs)
        
        
    def update(self):
        self.operation = self.operation_set.get(status=apps.get_model("core", "Operation").ACTIVE)
        self.location = self.operation.location
        self.worker = self.operation.worker
        self.save()
        
        
class Operation(models.Model):
    # Calculated Fields
    op_id = models.CharField("Operation ID", max_length=30, primary_key=True)
    link_slug = models.CharField("Link Slug", max_length=30, unique=True, editable=False)   
    abs_link = models.CharField("Link", max_length=30, unique=True, editable=False)
    active = models.BooleanField("Active", default=False, editable=False)
    display = models.BooleanField("Display", default=True, editable=False)

    # Output Fields
    actual_set = models.FloatField("Actual Set", blank=True, null=True)
    actual_run = models.FloatField("Actual Run", blank=True, null=True)
    actual_insp = models.FloatField("Actual Inspection", blank=True, null=True)
    actual_oneoff = models.FloatField("Actual One-Off", blank=True, null=True)
    actual_fullbatch = models.FloatField("Actual Full Batch", blank=True, null=True)
    actual_start_time = models.DateTimeField("Actual Start", blank=True, null=True)
    actual_end_time = models.DateTimeField("Actual End", blank=True, null=True)
    last_action_time = models.DateTimeField("Last Change", editable=False, blank=True, null=True)
    num_scrap = models.IntegerField("Qty Scrapped", null=True, blank=True)
        
    # Operation Overall Status
    NONE = None
    PENDING = "Pending"
    ACTIVE = "Active"
    COMPLETE = "Complete"
    STATUS_CHOICES = [(PENDING, 'Pending'), (ACTIVE, 'Active'), (COMPLETE, 'Complete'), (NONE, None)]
    status = models.CharField("Op Status", max_length=10, choices=STATUS_CHOICES, default=PENDING, editable=False, null=True, blank=True)
    
    # Interim Inspection
    
    SETUP = "Setup"
    ONEOFF = "One-Off"
    INTERIM = "Interim Inspection"
    FULLBATCH = "Full Batch"
    
    #Order is important - do not change
    PHASE_CHOICES = [(NONE, NONE), 
                     (PENDING, PENDING), 
                     (SETUP, SETUP), 
                     (ONEOFF, ONEOFF), 
                     (INTERIM, INTERIM), 
                     (FULLBATCH, FULLBATCH), 
                     (COMPLETE, COMPLETE)]
    PHASE_LIST = [e[0] for e in PHASE_CHOICES]
    phase = models.CharField("Phase", max_length=20, choices=PHASE_CHOICES, default=NONE, null=True, blank=True)
    
    # Relationships
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Worker")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Location")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="Job")
    #paired_op = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name="Paired Operation")
    
    # Entered Fieldss
    issue_no = models.CharField("Issue No.", max_length=1, blank=True, null=True)
    op_no = models.IntegerField("Op No.")
    
    # Entered Fields - Optional
    part_no = models.IntegerField("Part No.", blank=True, null=True)
    upload_id = models.IntegerField("Upload ID", blank=True, null=True)    
    name = models.CharField("Op Name", max_length=100, blank=True, null=True)
    drg_no = models.CharField("Drg No.", max_length=50, blank=True, null=True)
    start_time = models.DateTimeField("Start Time", blank=True, null=True)
    end_time = models.DateTimeField("Planned Finish", blank=True, null=True)
    planned_set = models.FloatField("Planned Set Mins", blank=True, null=True)
    planned_run = models.FloatField("Planned Run Mins", blank=True, null=True)
    insp_bool = models.BooleanField("Inspection T/F", default = False)
    op_note = models.CharField("Note", max_length=500, blank=True, null=True)
    is_interim = models.BooleanField(default=False)
      
    def __str__ (self):
        return self.op_id
    
    def save(self, *args, **kwargs):
        op_id = str(self.job.work_no) + "/" + str(self.issue_no) + f'{self.op_no:03}'
        self.op_id = op_id if not self.is_interim else op_id+"I"
        self.link_slug = slugify(self.op_id)
        self.abs_link = "/operation/" + self.link_slug
        if self.insp_bool and self.phase == self.NONE:
            self.phase = self.PENDING    
            self.save()    
            create_interim_op(self)
            
        scrap = 0
        for e in self.entry_set.all():
            if e.data:
                d = json.loads(e.data)
                if "scrapCode" in d:
                    d["quantity"] = 0 if not d["quantity"] else int(d["quantity"])
                    scrap += int(d["quantity"])
        self.num_scrap = scrap
        super(Operation, self).save(*args, **kwargs)
        
    def add_entry(self, msg="Entry Added", **kwargs):      
        newEntry = apps.get_model("core", "Entry").objects.create(
            message=msg, dt=datetime.now(tz=pytz.utc).astimezone(TZINFO), job=self.job, operation=self, **kwargs)
        newEntry.save()
        self.job.save()
        
    def check_in(self, check_in_loc, worker=None):
        
        for op in self.job.operation_set.filter(op_no__lt=self.op_no):
            if op.status == self.ACTIVE:
                op.add_entry("Operation completed".format(op.op_id, check_in_loc.name),
                            location=check_in_loc)
                
            elif op.status == self.PENDING:
                op.add_entry("Operation skipped".format(op.op_id, check_in_loc.name),
                            location=check_in_loc)
                op.actual_start_time = stdDateTime()
                
            op.actual_end_time = stdDateTime()
            op.status = self.COMPLETE
            op.save()
            
        if check_in_loc != self.location:
            self.add_entry("Op changed {} -> {}".format(self.location.loc_id, check_in_loc.loc_id), location=check_in_loc)
            self.location = check_in_loc
        
        self.actual_start_time = stdDateTime()        
        self.last_action_time = stdDateTime()
        self.status=self.ACTIVE
        self.save()
        self.add_entry("Checked in at {}".format(check_in_loc.name), location=check_in_loc)             
        self.job.operation = self
        self.job.location = self.location
        self.job.worker = self.worker
        if check_in_loc ==  Location.objects.get(loc_id=Location.END):
            self.job.status = Job.COMPLETE
        elif check_in_loc != Location.objects.get(loc_id=Location.START):
            self.job.status = Job.ACTIVE
        self.job.save()
        
    def check_out(self, worker=None):
        self.status = self.COMPLETE
        self.actual_end_time = stdDateTime()
        self.add_entry("Op Completed")
        self.save()
        
        if self.location == Location.objects.get(loc_id=Location.INTERIM):
            nextloc = self.job.operation_set.filter(op_no=self.op_no).exclude(location=self.location).order_by("op_no")[0]
            self.job.location = nextloc.location
        else:
            nextloc = self.job.operation_set.filter(op_no__gt=self.op_no).exclude(is_interim=True).order_by("op_no")[0]
            
        self.job.operation = nextloc
        self.job.save()           
        
        if self.job.operation_set.exclude(status=Operation.COMPLETE).count() < 2:
            endop = self.job.operation_set.filter(status=Operation.PENDING)[0]
            endop.check_in(Location.objects.get(loc_id=Location.END))
            self.job.add_entry("Job Complete")
            self.job.status = Job.COMPLETE
            self.job.save()
                         

class ScrapCode(models.Model):
    id = models.CharField("SC-ID", max_length=30, primary_key=True)
    name = models.CharField("SC-ID", max_length=100)
    
    def __str__ (self):
        return self.id + " - " + self.name


class Entry(models.Model):
    id = models.BigAutoField("ID", primary_key=True)
    dt = models.DateTimeField("Time")
    undone = models.BooleanField("Undone", default=False)
    message = models.CharField("Message", max_length=200)
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    operation = models.ForeignKey(Operation, on_delete=models.SET_NULL, blank=True, null=True)
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
    data = models.TextField("Data", default=None, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super(Entry, self).save(*args, **kwargs)
        
    
    def __str__(self):
        return displayDT(self.dt) + " - " + self.message
    
class FieldDict(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    data = models.TextField(default='{}')
    name = models.TextField(null=True, blank=True)
    
    allModels = ["Worker", "Location", "Company", "Job", "Operation", "ScrapCode", "Entry"]
    ALL = tuple([(x, x) for x in allModels])
    model = models.CharField(max_length=20, choices=ALL, default=None, null=True, blank=True)
    
    def get(self):
        return eval(self.data)    
    
    def __str__(self):
        return self.name
    
    