from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import simplejson as json
import sys
import pprint
import time 
import atexit
import urllib2, base64, urllib
import operator, httplib, traceback
from threading import Thread
import xbmc, xbmcgui, math, xbmcplugin,xbmcaddon

global scriptId
scriptId='script.partibus'

def loadConfig():
    global config,scriptId
    config={}
    try:
        config["xbmcPort"] = int(xbmcaddon.Addon(id=scriptId).getSetting("xbmcPort"))
        config["pluginPort"] = int(xbmcaddon.Addon(id=scriptId).getSetting("pluginPort"))
        print "Config loaded xbmc port:%i plugin port:%i" % (config["xbmcPort"],config["pluginPort"])
        return True
    except:
        traceback.print_exc()
        dialog = xbmcgui.Dialog()
        quit = dialog.ok("Partybus Warning", "Please enter an number for both port entries", "in the Partibus configuration.")
        xbmcaddon.Addon(scriptId).openSettings()
        return False
    


# Determine if we're running in Simulation mode
sim = (len(sys.argv)>1 and sys.argv[1]=="-s")
print "Partybus script started, Simulation mode =", sim

ACTION_PREVIOUS_MENU = 10
class MyClass(xbmcgui.Window):
    def onAction(self, action):
        print "function onAction(%s)" % repr(action)
        if action == ACTION_PREVIOUS_MENU:
            self.close()

#mydisplay = MyClass()
#mydisplay.doModal()
#del mydisplay


global CLIENT_SESSION_MAX
CLIENT_SESSION_MAX = 3600 # 1 hour

class XBMCToolkit(object):
    def __init__(self):
        pass

    def youtubeUrlToUri(self, url):
        videoid=None
        #url = "http://www.youtube.com/watch?v=Q0q1gCsZykg"
        uargs = url.split('?')[1].split('&')
        print uargs
        for pair in uargs:
            print pair
            s = pair.split('=')
            for k,v in zip(s[:-1],s[1:]):
                if k=='v':
                    print "Youtube video id for URL '" + url + "' is '" +v+"'"
                    videoid=v
        if videoid != None:
            uri = "plugin://plugin.video.youtube/?action=play_video&videoid=" + videoid
            print uri
            return uri
        return None

    def sendXBMCRpc(self, postdata):
        global config
        try:
            base64string = base64.encodestring('%s:%s' % ("xbmc", "password")).replace('\n', '')
            headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain", "Authorization":"Basic %s" % base64string}
            conn = httplib.HTTPConnection("127.0.0.1:"+repr(config["xbmcPort"]))
            conn.request("POST", "/jsonrpc", postdata, headers)
            response = conn.getresponse()
            print response.status, response.reason
            data = response.read()
            #print data
            conn.close()
            return data
        except:
            print "Exception when trying to send XBMC RPC."
            traceback.print_exc()
            return ""

    def playyoutube(self, url):
        print "function playyoutube(%s)" % url
        uri = self.youtubeUrlToUri(url)
        if uri == None:
            print "ERROR: could not play youtube URL"
            return

        base64string = base64.encodestring('%s:%s' % ("xbmc", "password")).replace('\n', '')
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain", "Authorization":"Basic %s" % base64string}
        endpoint = "ubuntu.local:"+repr(8081)
        print 'Youtube endpoint : ' + endpoint
        conn = httplib.HTTPConnection(endpoint)
        url="/xbmcCmds/xbmcHttp?command=ExecBuiltin(PlayMedia("+urllib.pathname2url(uri)+"))"
        print "URL="+url
        conn.request("POST", url, "", headers)
        response = conn.getresponse()
        print response.status, response.reason
        data = response.read()
        print data
        conn.close()

    def printTargetList(self, playlist, msg):
        currentPos = playlist.getposition()
        currentSize = playlist.size()
        print "printTargetList : " + msg
        for i in range(0, currentSize):
            extra=""
            if i == currentPos:
                extra=" (current)"
            print repr(i) + ":" + playlist[i].getfilename() + extra

if not sim:
    class MyPlayer(xbmc.Player):        
        def __init__(self):
            print "__init__ MyPlayer"
            xbmc.Player.__init__( self )

        def onPlayBackEnded( self ):
            try:
                endpos = self.playlist.playlist.getposition()
                print "playback ended " + repr(endpos)
                if self.playlist.pos == (len(self.playlist.list) -1):
                    print "End of partibus list detected, clearing playlist"
                    self.playlist.pos = -1
                    self.playlist.list = []
            except:
                print "Exception in callback thread"
                traceback.print_exc()  
                
        def onPlayBackStopped( self ):
            try:
                print "playback stopped " + repr(self.playlist.playlist.getposition())
                #self.playlist.pos = -1
            except:
                print "Exception in callback thread"
                traceback.print_exc()

        def onPlayBackStarted( self ) :
            try:
                newpos = self.playlist.playlist.getposition()
                print "playback started, newpos:%s playlist_len:%s list_len:%s" % (repr(newpos), repr(len(self.playlist.playlist)), repr(len(self.playlist.list)))

                if len(self.playlist.list) <= 0:
                    self.playlist.pos = -1
                    print "Partibus list length is zero so setting pos to -1"
                    return
                
                validPosition = True
                if newpos != -1:                    
                    if not self.playlist.validateList():
                        print "WARNING: playlist has been tampered with"
                        validPosition = False

                        dialog = xbmcgui.Dialog()
                        quit = dialog.yesno("Partybus Warning", "The playlist was altered outside of Partybus.", "Do you want to quit Partybus?")
                        print "Quit=%i" % quit
                        if quit:
                            # Clear the partybus playlist
                            del self.playlist.list[:]
                            self.playlist.pos = -1
                            return        
                        else:
                            self.playlist.play(self.playlist.pos, False)
                            return

                if validPosition:
                    print "Updating playlist position to " + repr(newpos)
                    self.playlist.pos = newpos

                if self.playlist.pos >= len(self.playlist.list):
                    # Invalid position in playlist, reset
                    print "WARNING: invalid position reached in playlist"
                    self.playlist.pos = -1

            except:
                print "Exception in callback thread"
                traceback.print_exc()


  
class Playlist(object):
    def __init__(self):
        self.active = True
        self.list = []
        self.futurelist=[]
        self.toolkit = XBMCToolkit()
        self.pos = -1
        if not sim:
            self.supportedvideo = xbmc.getSupportedMedia('video').split('|')            
            self.supportedmusic = xbmc.getSupportedMedia('music').split('|')
            self.musicplaylist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            self.videoplaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            self.musicplaylist.clear()
            self.videoplaylist.clear()
            self.playlist = self.videoplaylist
            self.playerThread = Thread(target=self.callbackThread, args=())
            self.playerThread.start()

    def validateList(self):
        if len(self.playlist) != len(self.list):
            print "List lengths differ."
            return False

        if len(self.musicplaylist) > 0:
            print "Audio playlist not empty"
            return False

        index = 0
        for item in self.list:
            try:
                if item.filename != self.playlist[index].getfilename():                
                    print "List contents differ, index = %i, %s, %s" % (index,item.filename,self.playlist[index].getfilename())
                    return False
            except:
                print "Exception validating list"
                traceback.print_exc()
                return False
                
            index = index + 1

        return True
    
    def determineMediaType(self, uri):
        uri=uri.lower()
        for end in self.supportedvideo:
            if uri.endswith(end.lower()):
                return 'video'
        for end in self.supportedmusic:
            if uri.endswith(end.lower()):
                return 'music'
        if uri.startswith("http://www.youtube.") or uri.startswith("http://m.youtube."):
            return 'youtube'
        return 'unsupported'

    def callbackThread(self):
        self.player = MyPlayer()
        self.player.playlist = self
        while not xbmc.abortRequested:
            xbmc.sleep(1000)
        print "Callback thread ending"
    
    def play(self, index, rebuildonly):
        print "function play(%s,%s)" % (repr(index), repr(rebuildonly))
        if index < 0:
            index = 0
        if index >= len(self.list):
            print "ERROR: attempt to play beyond end of list, index=" + repr(index)
            return        

        self.videoplaylist.clear()
        self.musicplaylist.clear()
        for i in range(len(self.futurelist)):            
            self.playlist.add(self.futurelist[i].filename)
            if rebuildonly and i == self.pos:
                break

        if not rebuildonly:
            xbmc.executebuiltin('XBMC.SetVolume(0)')
            #self.player.stop()
            retries=10
            #while self.player.isPlaying() and retries>0:
            #    print "sleeping..."
            #    sleep(1)
            #    retries=retries-1
                
            
            if retries>0:    
                self.player.play(self.playlist)
                self.player.playselected(index)                
                self.pos=index

            xbmc.executebuiltin('XBMC.SetVolume(100)')

    def locateExistingItem(self, newitem):
        pos = self.pos
        if pos < 0 or pos >= len(self.list):
            return None
        for item in self.list[pos:]:
            if newitem.filename == item.filename:
                return item 
        return None


    def queueDir(self, path, clients, client):
        count = 0
        ok = True
        for root, subFolders, files in os.walk(path):
            for filename in files:
                filePath = os.path.join(root, filename)
                dettype = self.determineMediaType(filePath)
                if dettype != 'unsupported':
                    print filePath
                    self.queue(PlaylistItem({"uri":filePath}, client.UID), clients, False)
                    count = count + 1
                    if count > 50:
                        ok = False
                        break
            if not ok:
                break
        if count > 0:
            xbmc.executebuiltin('XBMC.Notification("%s queued %i %s", "%s")' % (client.UID, count, 'song' if count==1 else 'songs', path))

    def skip(self, uid, clients):
        pos = self.pos
        if pos < 0 or pos >= len(self.list):
            return
        if uid not in self.list[pos].skipList:
            self.list[pos].skipList.append(uid)
        if len(self.list[pos].skipList) >= int(math.ceil(len(clients)*0.51)):
            self.player.playnext()                  
            
    def queue(self, item, clients, guiNotifications):
        if item.valid:            
            dettype=self.determineMediaType(item.filename)
            print "Determined media type as " + dettype

            queueSuccess = True
            if dettype=='youtube':
                uri=self.toolkit.youtubeUrlToUri(item.filename)
                if uri != None:
                    # Convert to youtube plugin URI
                    item.filename=uri
                else:
                    queueSuccess = False
            else :
                if dettype=='unsupported':
                    queueSuccess = False

            if not queueSuccess:
                if guiNotifications:
                    xbmc.executebuiltin('XBMC.Notification("%s Queue Failed!", "%s")' % (item.owners[0], item.filename))
                print "Queue failed (%s):%s" % (item.owners[0],item.filename)
                return False

            existing = self.locateExistingItem(item)
            if existing != None:
                if item.owners[0] not in existing.owners:
                    print "Item already exists"
                    existing.owners.append(item.owners[0])
            else: 
                self.list.append(item)

            if guiNotifications:
                xbmc.executebuiltin('XBMC.Notification("%s Queued", "%s")' % (item.owners[0], item.filename))
            print "Queued (pos:%i, len:%i) : %s" % (self.pos, len(self.list), str(item))
            self.buildPlaylist(clients)
            if self.pos == -1:
                # If we're stopped, then continue at end of the list
                #self.player.stop()
                self.play(len(self.list)-1, False)
            else:
                # if there's a pos set, but nothing is currently playing, continue at pos...
                if not self.player.isPlayingVideo() and not self.player.isPlayingAudio():
                    self.play(self.pos, False)

            return True
        else:
            print "Could not queue item : " + str(item)
            return False

    def buildPlaylist(self, clients):
        # Clear list after current position...
        if not sim:
            self.play(self.pos, True)
        self.futurelist=self.list
        self.reorder(self.pos, clients)

    # Recursive
    def reorder(self, pos, clients):
        # Score users based on when they last had a play
        index = 0
        lastplayed = {}        
        if pos >= 0:
            for item in self.list[:pos+1]:
                lastplayed[item.owners[0]] = pos - index
                index += 1

        # Find users who haven't had a play yet, score them higher than users who have had a play
        for client in clients:
            if not client in lastplayed:
                lastplayed[client] = pos + 1

        #print "lastplayed : " + repr(lastplayed)

        # Sort so that users with least plays comes first
        x = sorted(lastplayed.iteritems(), key=operator.itemgetter(1), reverse=True)
        print "Reorder("+repr(pos)+") priority: " + repr(x)
        priorityusers = map(lambda x:x[0], x)

        # Determine the highest score of anyone who has requested a song,
        # this shall be the power that someone who +1's a song shall get.
        voteScore=x[0][1]
        maxScore=0

        # Calculate a score for each song in the future playlist
        for i in range(pos+1, len(self.list)):
            score=0
            requester=self.list[i].owners[0]
            numVoters=len(self.list[i].owners[1:])
            score+=lastplayed[requester] + numVoters*voteScore
            self.list[i].score=score
            if score>maxScore:
                maxScore=score
            print "calc [%i] %i %s" % (pos-self.pos, self.list[i].score, self.list[i].filename)

        songsLeft=False
        for j in range(pos+1, len(self.list)):
            songsLeft=True
            if self.list[j].score==maxScore:
                print "win [%i] %s" % (pos-self.pos, self.list[j].filename)
                self.playlist.add(self.list[j].filename)                    
                self.futurelist.insert(pos+1, self.futurelist.pop(j))
                self.reorder(pos+1, clients)
                return
                
        if songsLeft:
            print "ERROR: invalid position reached while building playlist. maxScore=%i" % maxScore    

class PlaylistItem(object):
    def __init__(self, jData, owner):
        self.filename = jData["uri"]
        self.owners = [owner]
        self.valid = True
        self.created = int(time.time())
        self.skipList = []
        self.score=0

    def __str__(self):
        return "Item(file:" + self.filename +", owners:"+str(len(self.owners))+", valid:"+repr(self.valid)+")"


class ClientController(object):
    def __init__(self, UID):
        self.UID = UID
        self.timeUpdated = int(time.time())

    def __str__(self):
        return self.UID

    def update(self):
        self.timeUpdated = int(time.time())
        

class RequestHandler(BaseHTTPRequestHandler):
    clients = {}
    playlist = Playlist()


    def rpcResp(self, jsonId, error, respObj):
        resp = {}
        resp["id"]=jsonId
        if error:
            resp["result"]=None 
            resp["error"]=respObj
        else:
            resp["result"]=respObj
            resp["error"]=None            
        return json.dumps(resp)

    def _writeheaders(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        self._writeheaders()

    def do_GET(self):
        self.send_error(501, "Unsupported method 'GET'")

    def do_POST(self):
        varLen = int(self.headers['Content-Length'])
        postData = self.rfile.read(varLen)
        print "POST : '" + postData + "'"
        try:
            decoded = json.loads(postData)
        except:
            self.send_error(501, self.rpcResp(None, True, "Internal error."))
            return
        
        if ("params" in decoded and "id" in decoded and "method" in decoded):
            op = "operation_"+self.path[1:] + "_"+ decoded["method"]
            #print "check op " + op
            func = getattr(self, op, None)
            if callable(func):
                print "Calling operation :'" + op + "' with POST data="+postData
                func(decoded["params"], decoded["id"])
            else:
                self.send_error(501, self.rpcResp(decoded["id"], True, "No operation at this context path."))
        else:
            self.send_error(501, self.rpcResp(None, True, "Request is not a valid JSON-RPC request."))

    def getClientUid(self, jData):
        if "UID" in jData:
            return jData["UID"]
        else:
            return ""

    def cleanUpClients(self):
        global CLIENT_SESSION_MAX
        fordeletion = []
        for k, v in RequestHandler.clients.iteritems():
            if v.timeUpdated < int(time.time()) - CLIENT_SESSION_MAX:
                print "Client '" + k + "' : session has expired."
                fordeletion.append( k )

        for todel in fordeletion:
            del(RequestHandler.clients[todel])

    def getClientObject(self, uid):
        if len(uid) == 0:
            return None

        if uid in RequestHandler.clients:
            RequestHandler.clients[uid].update()
        else:
            RequestHandler.clients[uid] = ClientController(uid)

        self.cleanUpClients()
        print "Currently aware of " + repr(len(RequestHandler.clients)) + " clients"
        return RequestHandler.clients[uid]

    def operation_jsonrpc_test(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        print "operation test for UID:" + uid
        pprint.pprint(jData)
        RequestHandler.playlist.toolkit.playyoutube("http://www.youtube.com/watch?v=S3yHbf7XEXU&feature=related")
        client = self.getClientObject(uid)
        if client != None:
            pass

        self.send_response(200, self.rpcResp(jsonId, False, [1]))

    def operation_jsonrpc_play(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        client = self.getClientObject(uid)
        if client != None:
            RequestHandler.playlist.queue(PlaylistItem(jData, client.UID), RequestHandler.clients, True)
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(jsonId, False, [1]))
        else:
            self.send_error(501, self.rpcResp(None, True, "Unable to determine client for UID:"+repr(uid)))       

    def operation_jsonrpc_skip(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        client = self.getClientObject(uid)
        if client != None:
            RequestHandler.playlist.skip(client.UID, RequestHandler.clients)
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(jsonId, False, [1]))
        else:
            self.send_error(501, self.rpcResp(None, True, "Unable to determine client for UID:"+repr(uid)))       


    def operation_jsonrpc_playdir(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        client = self.getClientObject(uid)
        if client != None:
            print "jData:" + str(repr(jData))
            RequestHandler.playlist.queueDir(jData["uri"], RequestHandler.clients, client)
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(jsonId, False, [1]))
        else:
            self.send_error(501, self.rpcResp(None, True, "Unable to determine client for UID:"+repr(uid)))       

    def operation_jsonrpc_getsupported(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        client = self.getClientObject(uid)
        if client != None:
            print "jData:" + str(repr(jData))

            result={'audio': RequestHandler.playlist.supportedmusic, 'video': RequestHandler.playlist.supportedvideo}
                        
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(jsonId, False, result))
        else:
            self.send_error(501, self.rpcResp(None, True, "Unable to determine client for UID:"+repr(uid)))       


    def operation_jsonrpc_getplaylist(self, jData, jsonId):
        uid = self.getClientUid(jData)    
        client = self.getClientObject(uid)
        if client != None:
            print "jData:" + str(repr(jData))

            result={'position': RequestHandler.playlist.pos}
            contents=[]
            for x in RequestHandler.playlist.list:
                contents.append(x.filename)
            result['contents']=contents
            

            #RequestHandler.playlist.queueDir(jData["uri"], RequestHandler.clients, client)
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(jsonId, False, result))
        else:
            self.send_error(501, self.rpcResp(None, True, "Unable to determine client for UID:"+repr(uid)))       

        

    def addCrossSiteRequestHeaders(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Max-Age', '1000')
        self.send_header('Access-Control-Allow-Headers', '*')

    def operation_jsonrpc_route(self, jData, jsonId):
        uid = self.getClientUid(jData)
        print "operation route for UID:" + repr(uid)

        client = self.getClientObject(uid)
        if client != None and "payload" in jData:
            response=RequestHandler.playlist.toolkit.sendXBMCRpc(json.dumps(jData["payload"]))
            self.wfile.write("HTTP/1.0 200 OK\n")
            self.send_header('Server', self.version_string())
            self.send_header('Date', self.date_time_string())
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_response(501, 'Internal Error');
            self.send_header('Content-type', 'text/html')
            self.addCrossSiteRequestHeaders()
            self.end_headers()
            self.wfile.write(self.rpcResp(None, True, "Message format error, UID:"+repr(uid)))



global config        
if (loadConfig()):
    serveraddr = ('', config["pluginPort"])
    srvr = HTTPServer(serveraddr, RequestHandler)
    srvr.socket.settimeout(3)
    try:
        xbmc.executebuiltin('XBMC.Notification("Partibus", "Started")')
        while not xbmc.abortRequested:
            srvr.handle_request()
    except:
        print "ERROR: caught exception"
else:
    print "ERROR: loading config"
xbmc.executebuiltin('XBMC.Notification("Partibus", "Ended")')
print "Partybus script ended"

