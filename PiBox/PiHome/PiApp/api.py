#coding=utf-8
from django.shortcuts import render
from django import forms
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required  
from django.db import models
import json as simplejson   

from models import *
from forms import *

from common import client
from common import globaldata
from common import utils
from common import callback

def login_api(request):           
    if request.method == 'POST':  
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user)  
            ret = {'msg':'ok'}    
            ret['firstname'] = user.first_name
            ret['lastname'] = user.last_name
            return HttpResponse(simplejson.dumps(ret))   
        else:
            return HttpResponse(simplejson.dumps({'msg':'fail'}))   

def logout_api(request):
    logout(request)
    return HttpResponse(simplejson.dumps({'msg':'ok'}))   

def check_username(request):  
    if request.method == 'GET':  
        try:  
            if utils.validateEmail(request.GET['username'])  == 0:
                return HttpResponse(simplejson.dumps({'msg':'Please enter a valid email format'}))  
            user = PiUser.objects.get(username = request.GET['username'])
            if user is not None:  
                return HttpResponse(simplejson.dumps({'msg':'Username already exists'}))  
        except:  
            return HttpResponse(simplejson.dumps({'msg':'Username can be used'}))  

def check_login(request):  
    if request.user.is_authenticated():
        return HttpResponse(simplejson.dumps({'msg':'ok'}))  
    else:
        return HttpResponse(simplejson.dumps({'msg':'fail'}))  


def register_api(request):    
    pisettings_instance = globaldata.getclient()
    if pisettings_instance.enable_register != True:
        return HttpResponse("You are not be allowed to register") 
    form = PiRegisterForm(request.POST or None)
    if form.is_valid():
        first_name=form.cleaned_data['first_name']
        last_name=form.cleaned_data['last_name']      
        email = form.cleaned_data['email'] 
        password=form.cleaned_data['password1']
        user = PiUser.objects.create_user(email, email, password)    
        if user is not None:  
            user.first_name =  first_name
            user.last_name = last_name
            user.is_staff = True  
            user.save()  
            return HttpResponse(simplejson.dumps({'msg':'ok'}))  
        else:  
            return HttpResponse(simplejson.dumps({'msg':'fail'}))  

def account_change_api(request):
    user = PiUser.objects.get(username = request.user.username)
    form = PiAccountForm(request.POST or None, instance = user)
    if form.is_valid():
        user.first_name=form.cleaned_data['firstname']
        user.last_name=form.cleaned_data['lastname']      
        if(form.cleaned_data['password1']  !=  "") :  
            password=form.cleaned_data['password1']
            if password != None:
                user.set_password(password)
        user.save()
        return HttpResponse(simplejson.dumps({'msg':'ok'}))  


def account_info_api(request):
    user = PiUser.objects.get(username = request.user.username)
    ret = {'msg':'ok'}
    ret[firstname] = user.first_name
    ret[lastname] = user.last_name
    return HttpResponse(simplejson.dumps({'msg':'ok'}))  


def piclient_api(request):
    pisettings_instance = globaldata.getclient()

    message = { "title" : "status"}
    if request.method == 'GET':
        try:
            message['cmd'] =  request.GET['cmd'] ;
        except: 
            message['cmd'] =  '' ;

    pi_ret = client.socketjson_send_recv(pisettings_instance.ip,  pisettings_instance.port, message)

    return HttpResponse(simplejson.dumps(pi_ret.message))  


def nas_api(request):
    pisettings_instance = globaldata.getclient()
      
    message = { "title" : "nas"}
    if request.method == 'GET':
        try:
            message['cmd'] =  request.GET['cmd'] ;
        except: 
            message['cmd'] =  '' ;

    pi_ret = client.socketjson_send_recv(pisettings_instance.ip,  pisettings_instance.port, message)

    return HttpResponse(simplejson.dumps(pi_ret.message))  


def server_api(request):
    pi_ret = {'version': globaldata.VERSION}
    return HttpResponse(simplejson.dumps(pi_ret))


def dashboard_api(request):
    pisettings_instance = globaldata.getclient()

    pi_ret = {'nas': globaldata.NasEnable}
    if(client.socket_test(pisettings_instance.ip,  pisettings_instance.port)):
        pi_ret['connection'] = "TRUE"
    else:
        pi_ret['connection'] = "FALSE"
    pi_ret['app_num'] =   len(globaldata.AppList)

    pi_ret['user_count'] = PiUser.objects.count()

    return HttpResponse(simplejson.dumps(pi_ret))


def settings_account_api(request):
    user = PiUser.objects.get(username = request.user.username)
    form = PiAccountForm(request.POST or None, instance = user)
    if form.is_valid():
        user.first_name=form.cleaned_data['first_name']
        user.last_name=form.cleaned_data['last_name']      
        if(form.cleaned_data['password1']  !=  ""):   
            password=form.cleaned_data['password1']
            if password != None:
                user.set_password(password)
        user.save()
    t = get_template('settings/api_account.html')
    c = RequestContext(request,locals())


def settings_general_api(request):
    pisettings_instance = globaldata.getclient()
    form = PiSettingsForm(request.POST or None, instance = pisettings_instance)
    if form.is_valid():
        form.save()
        form = PiSettingsForm(instance = pisettings_instance)
    t = get_template('settings/api_general.html')
    c = RequestContext(request,locals())
    return HttpResponse(t.render(c))

def kill_process_api(request):
    try:
        pid = request.REQUEST['pid']
        os.system("kill -9 " + pid)  
        ret = {'msg':'ok'}
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret)) 


###################my home##################
def remove_device_by_id_json(request):
    try:
        device_id = request.REQUEST['device_id']
        device_instance = Device.objects.get(id =device_id)    
        device_instance.delete()
        ret = {'msg':'ok'}
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))     

def get_device_by_id_json(request):
    try: 
        device_id = request.REQUEST['device_id']
        device_instance = Device.objects.get(id =device_id)    
        ret = {'msg':'ok', 'title':device_instance.name,'location':device_instance.describe,\
                'about':device_instance.location,'x':device_instance.x,'y':device_instance.y,}
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))  

def get_sensor_by_device_id_json(request):
    try: 
        device_id = request.REQUEST['device_id']
        device_instance = Device.objects.get(id = device_id)    
        sensors = device_instance.sensor.all()   
        ret_sensor = list()
        for sensor in sensors:
            a = dict()
            a['id'] = sensor.id
            a['title'] = sensor.name
            a['about'] = sensor.describe
            a['type'] = sensor.sensor_class 
            a['unit_symbol'] = sensor.unit   
            

            ret_sensor.append(a)
        ret = {'msg':'ok'}     
        ret['sensor'] = ret_sensor   
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret)) 

def remove_sensor_by_id_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        sensor_instance.delete()
        ret = {'msg':'ok'}
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))   

def add_sensor_callback_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        callback = request.REQUEST['callback_file']
        sensor_instance.callback_file = callback
        try:
            callback_value = float(request.REQUEST['callback_value'])
            callback_condition = request.REQUEST['callback_condition'] 
            sensor_instance.callback_value = callback_value
            sensor_instance.callback_condition = callback_condition
        except:
            pass
        sensor_instance.save()
        ret = {'msg':'ok'}
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))  

def get_sensor_callback_json(request):
    try: 
        ret = {'msg':'ok'}
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)          
        ret['callback_file'] = sensor_instance.callback_file  
        if sensor_instance.sensor_class == 'n':
            ret['callback_value'] = sensor_instance.callback_value 
            ret['callback_condition'] = sensor_instance.callback_condition 
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret)) 
#######################################
##           MYHOME_API             ###
#######################################
def new_datapoint_json(request):
    # device_id = request.REQUEST['device_id']
    # device_instance = Device.objects.get(id = device_id) 
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "s":
            try:
                datapoint_instance = SwitchDatapoint.objects.get(sensor = sensor_instance)  
            except:
                datapoint_instance = SwitchDatapoint.objects.create(sensor = sensor_instance)
            if int(request.REQUEST['status']) == 1:
                callback.switch_callback(sensor_instance, 1)
                datapoint_instance.status = True
            elif int(request.REQUEST['status']) == 0:
                callback.switch_callback(sensor_instance, 0)
                datapoint_instance.status = False
            datapoint_instance.save()
        elif sensor_instance.sensor_class == "n":
            if request.method == 'POST':
                req = simplejson.loads(request.body)
                if isinstance(req, list):
                    for item in req:
                        NumDatapoint.objects.create(sensor = sensor_instance, key = item['key'], value = item['value'] ); 
                        try:
                            callback.num_callback(sensor_instance, item['value'], item['key'])  
                        except:
                            pass
                else:
                    NumDatapoint.objects.create(sensor = sensor_instance, key = req['key'], value = req['value'] );  
                    try:  
                        callback.num_callback(sensor_instance, req['value'], req['key'])  
                    except:
                            pass
            else:
                NumDatapoint.objects.create(sensor = sensor_instance, key = request.REQUEST['key'], value = request.REQUEST['value'] )
                try:
                    callback.num_callback(sensor_instance, request.REQUEST['value'], request.REQUEST['key'])  
                except:
                    pass
        elif sensor_instance.sensor_class == "p":
            PicDatapoint.objects.create(sensor = sensor_instance, key = request.REQUEST['key'], pic_file = request.FILES['value'] )     
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))   

def get_datapoint_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)          
        # sensors = device_instance.sensor.all()   
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "s":
            try:
                datapoint_instance = SwitchDatapoint.objects.get(sensor = sensor_instance)  
            except:
                datapoint_instance = SwitchDatapoint.objects.create(sensor = sensor_instance)
            ret['status'] = datapoint_instance.status
        elif sensor_instance.sensor_class == "n":
            datapoint_instance = NumDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key'])
            ret['value'] = datapoint_instance.value
        elif sensor_instance.sensor_class == "p":
            key = request.REQUEST['key']
            if (key == 0) or (key == '0'):
                datapoint_instance = PicDatapoint.objects.filter(sensor = sensor_instance).order_by("-key")[0]
            else:
                datapoint_instance = PicDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key']) 
            ret['value'] = settings.MEDIA_URL + str(datapoint_instance.pic_file)   
            ret['key'] =  str(datapoint_instance.key)  
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))   


def edit_datapoint_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "n":
            datapoint_instance = NumDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key'])
            datapoint_instance.value = request.REQUEST['value']
            datapoint_instance.save()
            try:
                callback.num_callback(sensor_instance, request.REQUEST['value'], request.REQUEST['key'])
            except:
                pass 
        elif sensor_instance.sensor_class == "p":
            datapoint_instance = PicDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key']) 
            datapoint_instance.value = request.FILES['value']
            datapoint_instance.save()
        
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))   

def remove_datapoint_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "n":
            datapoint_instance = NumDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key'])
            datapoint_instance.delete()
        elif sensor_instance.sensor_class == "p":
            datapoint_instance = PicDatapoint.objects.get(sensor = sensor_instance, key = request.REQUEST['key'])
            datapoint_instance.delete()      
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))   

def history_datapoint_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)  
        try:   
            start = request.REQUEST['start']
            end = request.REQUEST['end']
            interval = int(request.REQUEST['interval'])
            exact = True
        except:
            exact = False

        # sensors = device_instance.sensor.all()   
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "n":
            if exact == False: #ret 20 datapoints
                datapoints = NumDatapoint.objects.filter(sensor = sensor_instance).order_by("-key")[0:20]
                ret_data = list()
                for datapoint in datapoints:   
                    a = dict()
                    a['key'] = str(datapoint.key)
                    a['value'] = datapoint.value 
                    ret_data.append(a)
                ret['datapoint'] = ret_data 
            else:
                datapoints = NumDatapoint.objects.filter(sensor = sensor_instance, key__gte = start, key__lte = end)
                ret_data = list()

                i = 0
                last_in = 0
                for datapoint in datapoints:
                    if i > 0:
                        timedelta = int((datapoints[i].key - last_in).seconds)  
                        if timedelta >= interval :  
                            last_in = datapoints[i].key
                            a = dict()
                            a['key'] = str(datapoint.key)
                            a['value'] = datapoint.value 
                            ret_data.append(a)
                    else:
                        last_in = datapoints[0].key
                        a = dict()
                        a['key'] = str(datapoint.key)
                        a['value'] = datapoint.value 
                        ret_data.append(a)
                    i += 1   
                ret['datapoint'] = ret_data     
        elif sensor_instance.sensor_class == "p": 
            if exact == False: #ret 20 datapoints
                datapoints = PicDatapoint.objects.filter(sensor = sensor_instance).order_by("-key")[0:20]
                ret_data = list()
                for datapoint in datapoints:   
                    a = dict()
                    a['key'] = str(datapoint.key)
                    a['value'] = settings.MEDIA_URL + str(datapoint.pic_file) 
                    ret_data.append(a)
                ret['datapoint'] = ret_data 
            else:
                datapoints = PicDatapoint.objects.filter(sensor = sensor_instance, key__gte = start, key__lte = end)
                ret_data = list()

                i = 0
                last_in = 0
                for datapoint in datapoints:
                    if i > 0:
                        timedelta = int((datapoints[i].key - last_in).seconds)  
                        if timedelta >= interval :  
                            last_in = datapoints[i].key
                            a = dict()
                            a['key'] = str(datapoint.key)
                            a['value'] = settings.MEDIA_URL + str(datapoint.pic_file) 
                            ret_data.append(a)
                    else:
                        last_in = datapoints[0].key
                        a = dict()
                        a['key'] = str(datapoint.key)
                        a['value'] = settings.MEDIA_URL + str(datapoint.pic_file) 
                        ret_data.append(a)
                    i += 1   
                ret['datapoint'] = ret_data     
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))      

def key_range_datapoint_json(request):
    try:
        sensor_id = request.REQUEST['sensor_id']
        sensor_instance = Sensor.objects.get(id = sensor_id)     

        # sensors = device_instance.sensor.all()   
        ret = dict()
        ret['msg'] = 'ok'
        if sensor_instance.sensor_class == "n":
            datapoints = NumDatapoint.objects.filter(sensor = sensor_instance)
            val = datapoints.aggregate(models.Max('key'))['key__max']
            if val != None:
                ret['max'] = str(val)
                ret['max'] = ret['max'][ :ret['max'].find('+')]
            val = datapoints.aggregate(models.Min('key'))['key__min']
            if val != None:
                ret['min'] = str(val)
                ret['min'] = ret['min'][ :ret['min'].find('+')]
        elif sensor_instance.sensor_class == "p":
            datapoints = NumDatapoint.objects.filter(sensor = sensor_instance)
            val = datapoints.aggregate(models.Max('key'))['key__max']
            if val != None:
                ret['max'] = str(val)
                ret['max'] = ret['max'][ :ret['max'].find('+')]
            val = datapoints.aggregate(models.Min('key'))['key__min']
            if val != None:
                ret['min'] = str(val)
                ret['min'] = ret['min'][ :ret['min'].find('+')]
    except:
        ret = {'msg':'fail'}
    return HttpResponse(simplejson.dumps(ret))      