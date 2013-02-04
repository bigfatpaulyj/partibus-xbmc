from django.template import Context, loader
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
import operator, httplib, traceback, os, json
from partibus.models import Server
from django.contrib.auth.models import User
from django.db import DatabaseError


@login_required(login_url="/login/?next=/")
def filelist(request, path="/"):
    global config

    if path != "/":
        path = "/" + path

    servers=Server.objects.all()

    return render_to_response('filelist.html', {'path':path, 'baseurl':reverse('logic.views.filelist'), 'clientIP':request.META['REMOTE_ADDR'], 'servers':servers},
context_instance=RequestContext(request)  )


@login_required(login_url="/login/?next=/")
def editserver(request):
    try:
        print "edit, data:" + request.raw_post_data
        servers=Server.objects.all()
        incoming=json.loads(request.raw_post_data)
        
        server=""
        if (incoming["id"]==-1):
            print "Creating new Server"
            server=Server()
        else:        
            print "Loading server id:"+incoming["id"]
            server=Server.objects.get(pk=incoming["id"])

        server.description=incoming["description"]
        server.hostname=incoming["hostname"]
        server.port=incoming["port"]
        server.user=request.user
        server.save()
        print "Saved."

        response={"result":"success"}
    except:
        response={"result":"failure"}
    print "Response:"+json.dumps(response)
    return HttpResponse(json.dumps(response), mimetype='application/json')        
        
        

@login_required(login_url="/login/?next=/")
def account(request):
    return render_to_response('account.html')

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
def createaccount(request):
    msg=""
    success=False
    try:
        email=request.REQUEST["email"]
        pass1=request.REQUEST["password1"]
        pass2=request.REQUEST["password2"]
        if len(pass1)<6:
            raise MyError("Password must be at least 6 chars")
        if pass1!=pass2 or len(pass1)<6:
            raise MyError("Password mismatch")
        user = User.objects.create_user(email, email, pass1)
        user.save()

        msg=""
        success=True
    
    except MyError as e:
        msg=e.__str__()
    except DatabaseError as e:
        msg="Account already exists"
    except:
        pass

    return render_to_response('createaccount.html', {'error':msg, 'success':success}, context_instance=RequestContext(request)  )



