$.mobile.defaultPageTransition = 'fade';
Actions = { root : "root", dir : "dir", file : "file" };
var itemContext="";
var logtraffic=true;
var enabledTypes=["mp3","flac","wav","wma","m4a"];
var csrftoken = getCookie('csrftoken');
var serverList=new ServerList($("#serverlist"));

var entriesPerPage=5;
var state=new State();

function State()
{
    this.path="/";
    this.depth=0;
    this.supported=[];
    this.endpoint="";
    this.pathdb=[];
    this.index=0;
    this.filter="";
}

String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};


if (typeof String.prototype.startsWith != 'function') {
  // see below for better implementation!
  String.prototype.startsWith = function (str){
    return this.indexOf(str) == 0;
  };
}


$(document).on('pageinit', bindEvents);
function bindEvents()
{
    sl="#slider-1";
    console.log("Binding events.");

    $(sl ).bind( "change", 
		 function(event, ui) 
		 {
		     console.log("slide");
		     if (state.pathdb[state.path]== undefined) return; 
		     
		     var newindex=parseInt($(this).val());
		     if (newindex!=state.index && newindex>0)
		     {
			 console.log("redrawing due to slide");
			 
			 state.index=newindex;
			 console.log(state.index);
			 redrawLib();		  
		     }  
		 });

	$( sl ).on( 'slidestop', 
		    function( event ) 
		    { 
			console.log("slide stop");
			if (state.pathdb[state.path]== undefined) return; 
			console.log("redrawing due to slide stop");

			state.index=parseInt($(this).val());
			console.log(state.index);
			redrawLib();		
		    });


    $("#listfilter").bind("propertychange keyup input paste", function(event){
	console.log("search");
	var newfilter=$(this).val();
	updateFilter(newfilter);
    });

    $('.ui-input-clear').live('click', function(e){
	console.log("Click on filter clear.");
	updateFilter("");
    });
}    

function updateFilter(newfilter)
{
	if (newfilter!=state.filter)
	{
	    console.log("redrawing due to filter change");
	    state.filter=newfilter;
	    state.index=0;
	    redrawLib();
	}
}

$(document).bind( "pagebeforechange", 
		  function( e, data ) 
		  {
		      console.log('pagebeforechange to page:' + data.toPage + " " + (typeof data.toPage));
		      
		      // We only want to handle changePage() calls where the caller is
		      // asking us to load a page by URL.
		      if ( typeof data.toPage === "string" ) 
		      {				
			  var u = $.mobile.path.parseUrl( data.toPage );
			  var searchstring = baseUrl+"files";
			  var urlprefix = u.pathname.substring(0, searchstring.length);
			  
			  console.log("urlprefix="+urlprefix + ",topage="+u.hash);

			  			  
			  if (u.hash !="#chooseserver" && state.supported.length==0)
			  {
			      connect();
			  }

			  if (u.hash.startsWith("#serverconfig"))
			  {
			      $("#serverconfig").show();
/*			      splits=u.hash.split("&")[0];
			      if (splits[0]=="edit")
			      {
				  id=splits[1];
				  var server=Server.getServerFromID(id);
				  $("#serverconfig_hostname").attr("value", server.hostname);
			      }*/
			  }

			  var drawList=false;
			  if (u.hash == "#nextpage")
			  {
				  state.index+=entriesPerPage;
				  drawList=true;
			  }
			  if (u.hash == "#prevpage")
			  {
				  if (state.index>=entriesPerPage)
					  state.index-=entriesPerPage;
			          else
				      state.index=0;
				  drawList=true;
			  }
			  
			  if (u.hash == "#account")
			  {
			      serverList.redraw();
			      return;
			  }
			  			  
			  if (u.hash.substring(0,3) == "#up") 
			      {
				  levels=parseInt(u.hash.substring(3));
				  if (isNaN(levels)) levels=1;	
				  if (levels>0)
				  {
				      console.log("jump up levels:"+levels);
					  state.path=getUpButtonPath(state.path,levels);
					  console.log("Up button, path=" + state.path);
					  state.index=0;
					  drawList=true;
				  }				 
			      }
			  
			  if (u.hash == "#editserver")
			  {
			      var postdata={
				  "id":-1, 
				  "description": $("#serverconfig_description").val(),
				  "hostname": $("#serverconfig_hostname").val(),
				  "port": $("#serverconfig_port").val()
			      };
			      
			      console.log("editserver"+postdata);
			      makeRequest(postdata, function() 
					  {
					      console.log("editserver successful");
					      //$.mobile.changePage("#account");
					      window.location.reload();
					  }, "/editserver/");
			  }

			  if (u.hash == "#connectserver")
			  {
			      state.endpoint='http://'+$("#serverselect").val()+'/jsonrpc';
			      console.log("Attempting to connect to : "+state.endpoint);
			      connect();
			  }
			  
			  if (u.hash == "#home")
			  {
			      displayHome();
			      return;
			  }
			  
			  if (u.hash == "#sources")
			  {
			      state.path="/";
			      state.depth=0;
			      drawList=true;
			  }

			  if (u.hash == "#chooseserver")
			  {
			      data.options.allowSamePageTransition=true;
			  }			  
			  
			  if (u.hash.length===0)
			  {
			      $.mobile.changePage("#library");
			  }

			  if (u.hash=="#library" || drawList)
			  {
			
			      redrawLib();
			  }
		      }
		  });




function buildListEntry(item)
{
    var theme="c";
    var split="";
    switch (item.filetype)
	{
	case "directory": 
	    //theme="d";
	    split+='<a href="#" class="dirContext">A</>';
	    if (item.file.endsWith(".pls") || item.file.endsWith(".m3u") || item.file.endsWith(".b4s"))
	    {
		return "";
	    }
	    break;
	case "file":		
	    found = false;
	    for (suffix in state.supported)
	    {
		if (item.file.endsWith(state.supported[suffix]))
		{
		    if (item.label.endsWith(state.supported[suffix]))
		    {
			// Chop the extension off the label if needs be
			item.label=item.label.substr(0,item.label.length-state.supported[suffix].length);
		    }
		    found = true;
		    break;
		}
	    }
	    enabled = false;
	    for (suffix in enabledTypes)
	    {
		if (item.file.endsWith(enabledTypes[suffix]))
		{
		    enabled = true;
		    break;
		}
	    }
	    if (!found || !enabled) return "";
	    break;
	}
    
    return '<li data-role="listview" data-split-icon="grid" data-theme="' + theme + '" data-icon="none"><a href="#" data-path="'+item.file+'" class="pathContext">'+item.label+'</a>'+split+'</li>';
}


function displayHome()
{
    
    console.log("Displaying home");
    var postdata = {"jsonrpc": "2.0", "params": {"UID": clientIP}, "id": "bjb7t3bw", "method": "getplaylist"};
    $.mobile.showPageLoadingMsg();
    postDataString = JSON.stringify(postdata);
    console.log("post:"+postDataString);
    $.post(state.endpoint, postDataString, function(data) {
	    console.log("data:"+data);
	    var output=JSON.parse(data);
	    var page=$.mobile.activePage;
	    var listview = page.find("ul[tunelist]");
	    var position = output["result"]["position"];
	    var contents = output["result"]["contents"];
	    var nowplaying = $('#nowplaying');

	    if (position>=0)
		{
		    nowplaying.html(contents[position]);
		}
	    	   
	    listview.empty();	    
	    $.each(contents, function(i, filename) {
		    if (i>position)
			{
			    item={'filetype':'file','file':filename, 'label':filename};
			    listview.append(buildListEntry(item));
			    console.log(item);		    
			}
		});	    
	    
	    listview.listview('refresh');	    
	    addContextToItems();
	    $.mobile.hidePageLoadingMsg();
	});    
}

function disconnected()
{
    $("#disconnectmessage").html("Error: Could not contact server.<p>");
    $.mobile.hidePageLoadingMsg();
    $.mobile.changePage("#chooseserver");
}

function queueYoutube()
{
    var url=$('#youtubeurl').attr('value');
    $('#youtubeurl').attr('value','');	
    var postdata = {"jsonrpc": "2.0", "params": {"uri":url, "UID":clientIP}, "id": "bjb7t3bw", "method": "play"};
    makeRequest(postdata, 
		function(data) {
		    console.log("data:"+data);
		    var output=JSON.parse(data);
		    var result = output["result"];		    
		    if (result[0]==1) console.log("URL added successfully.");	
		},
		state.endpoint
	       );
    return true;
}

function parseGetDirectoryResponse(listview, data,path)
{
    console.log("Index:"+state.index+",entriesPerPage:"+entriesPerPage);
    if (data!=undefined) 
    {
	// Cache the result, only store validated results
	state.pathdb[path]=Array();
	for (entry in data.files)
	{
	    if (buildListEntry(data.files[entry]) != "")
	    {
		state.pathdb[path].push(data.files[entry]);
	    }
	}	

	//var listitems = state.pathdb[path];
	state.pathdb[path].sort(function(a, b) {
	    var compA = a.label.toUpperCase();
	    var compB = b.label.toUpperCase();
	    return (compA < compB) ? -1 : (compA > compB) ? 1 : 0;
	})	
    }

    console.log("search results:");
    filterlist=Array();
    for (entry in state.pathdb[path])
    {
	if (state.pathdb[path][entry].label.toUpperCase().search(state.filter.toUpperCase()) > -1)
	{
	    filterlist.push(state.pathdb[path][entry]);
	}
    }

    // Update the position of the slider
    if (state.index >= filterlist.length) state.index=filterlist.length-1; //-=entriesPerPage;
    if (state.index < 0) state.index=0;
    var slider=$("#slider-1");
    slider.attr("max", filterlist.length-entriesPerPage);
    slider.attr("value", state.index);
    slider.slider('refresh');    

    var compound="";
    var entriesAdded=0;
    while (true)
    {
	var i=state.index+entriesAdded;
	if (i>=filterlist.length) break;
	listentry=buildListEntry(filterlist[i]);
	if (listentry!="")
	{
	    compound+=listentry;		
	}
	entriesAdded++;
	if (entriesAdded>=entriesPerPage) break;
    }

    // Update the index position text
    $("#indexreport").html(state.index+"-"+(state.index+entriesAdded)+" of "+filterlist.length);


    if (compound!="")
    {
	listview.html(compound);
    }
}

function parseGetSourcesResponse(listview, data)
{
    if (data.sources==undefined) return;
    console.log(JSON.stringify(data.sources));
    $.each(data.sources, function(i, item) {
	    console.log(item.file);
	    listview.append(buildListEntry(item));
	});
}



function makeRequest(postdata, callback, endpoint)
{
    if (endpoint.length<=0) return;
    postDataString = JSON.stringify(postdata);
    console.log("send to " + endpoint + " : "+postDataString);
    $.ajax({
        type: "POST",
        url: endpoint,
        data: postDataString,
        timeout: 2000, // in milliseconds
        success: callback,
        error: disconnected,
	beforeSend: function(xhr, settings) {
            if (settings.url!=state.endpoint) {
		xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
	}

    });
}

function redrawLibContinue(data)
{
    var action = determineAction(state.path);
    if (data!=undefined)
    {
	    if (logtraffic) console.log("data:"+data);
	    var output=JSON.parse(data);
	    var result = output["result"];
    }
    else result=undefined;
    var page=$("#library");//.mobile.activePage;
    var listview = page.find("ul[tunelist]");
    var pathview = page.find("p");

    switch (action)
    {
    case Actions.root: 
	    state.depth=0;
	    listview.empty();
	    parseGetSourcesResponse(listview, result);
	    pathview.html(getPathViewHtml(state.path));
	    listview.listview('refresh');
	    break;
    case Actions.dir: 
	    listview.empty();
	    parseGetDirectoryResponse(listview, result,state.path);
	    pathview.html(getPathViewHtml(state.path));
	    listview.listview('refresh');
	    break;
    case Actions.file:
	    if (result[0]==1) 
	    {
		    console.log("File added successfully.");
		    var filename = state.path.replace(/^.*[\\\/]/, '');
		    showNotification(page, "Queued: "+filename);
	    }
	    listview.find("li.ui-btn-active").removeClass('ui-btn-active');
	    // Set the path back to the parent dir
	    state.path=state.path.match(/^.+\//)[0]
	    break;
    default:
	    console.log("ERROR: invalid action.");
    }
	  	   				    	    
    $.mobile.hidePageLoadingMsg();
    if (action!=Actions.file) 
    {
	    addContextToItems();
    }	   
}

function determineAction(path)
{
   // determine the action
    var action = Actions.file;
    if (state.path=='/' && state.depth==0) 
	{
	    action=Actions.root;
	}
    else if (state.path.match(/\/$/)) action=Actions.dir;
    return action;
}

function redrawLib()
{
    // determine the action
    var action = determineAction(state.path);
    page=$.mobile.activePage;

    if (state.pathdb[state.path]==undefined)
    {
	$.mobile.showPageLoadingMsg();

	switch (action)
	{
	case Actions.root:
	    var postdata = {"jsonrpc": "2.0", "params": {"payload":{"id":"bjb7t3bw","jsonrpc":"2.0","method":"Files.GetSources","params":{"media":"music"}}, "UID": clientIP}, "id": "bjb7t3bw", "method": "route"};
	    break;
	case Actions.dir:
	    var postdata = {"jsonrpc": "2.0", "params": {"payload":{"id":"bjb7t3bw","jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":state.path}}, "UID": clientIP}, "id": "bjb7t3bw", "method": "route"}; 
	    break;
	case Actions.file:
	    var postdata = {"jsonrpc": "2.0", "params": {"uri":state.path, "UID":clientIP}, "id": "bjb7t3bw", "method": "play"};
	    break;
	default:
	    console.log("ERROR: invalid action.");
	}
	console.log(JSON.stringify(postdata));

	postDataString = JSON.stringify(postdata);
	if (state.endpoint.length<=0) return;
	if (logtraffic) console.log("post:"+postDataString);
	$.ajax({
            type: "POST",
            url: state.endpoint,
            data: postDataString,
            timeout: 2000, // in milliseconds
	    success: redrawLibContinue,
            error: disconnected
	});
    }
    else
    {
	redrawLibContinue(undefined);
    }    
}

function getParentPath(path)
{
    out = "/";
    splits=path.split('/');
    $.each(splits, function(i, item) {
	    if (item === "") return;
	    out += item + '/';
	});
    return out;
}

function filePathToPagePath(path)
{
    return baseUrl+'files'+path;
}



function getUpButtonPath(path,numlevels)
{
    if (state.depth-numlevels <= 0)
	{
	    state.depth=0;
	    return '/';
	}
	
    splits=path.split('/');
    combo="";
    for (i=0;i<splits.length-numlevels-1;i++) {
	combo+=splits[i]+'/';
    }
    console.log("getup before:"+state.depth);
    state.depth=state.depth-numlevels;
    console.log("getup after:"+state.depth);
    return combo;
}

function getPathViewHtml(path)
{
    out = "/";
    splits=path.split('/');
    combo = "";
    $.each(splits, function(i, item) {
	    if (item === "" ) return;
	    if (i>=splits.length-state.depth-1)
		{
		    link = '#up'+((splits.length)-(i)-(splits.length-state.depth-1)+1);
		    out += '<a href="'+link+'" > '+item+' </a> /';
		}
	    combo+="/"+item + "";
	});
    return out;
}

function queueDir(filename)
{
    //var filename = itemContext.replace(/^\/[^\/]+/,'');
    var postdata = {"jsonrpc": "2.0", "params": {"uri":filename, "UID":clientIP}, "id": "bjb7t3bw", "method": "playdir"};
    makeRequest(postdata, function(data) 
		{
		    console.log("data:"+data);
		    var output=JSON.parse(data);
		    var result = output["result"];
					 
		    if (result[0]==1) console.log("Directory added successfully.");	
		},
	       state.endpoint
	       );
}

function addContextToItems()
{
    $(".dirContext").click(
			   function()
			   {
			       // Set the global item context variable
			       itemContext=$(this).parent().find(".pathContext").data('path');
			       console.log('Dir queue itemcontext:'+itemContext);
			       queueDir(itemContext);
			       return true;
			   });
    $(".pathContext").click(
			   function()
			   {
			       // Set the global item context variable
			       itemContext=$(this).data('path');
			       state.path=itemContext;
			       console.log('Dir change itemcontext:'+itemContext);
			       state.depth++;
			       state.index=0;
			       redrawLib();
			       return false;
			   });

}

function connect()
{
    // stage 1
    if (state.endpoint !="" && state.endpoint!= undefined)
    {
	getSupported(connectContinue);
    }
}

function connectContinue()
{
    // stage 2
    $.mobile.changePage("/");
    $("#disconnectmessage").html("");
}

function showNotification(source, message) {
    $('.notification').remove();
    var notif = $('<div>').addClass('notification').html(message);		      
    $(source).after(notif);
    notif.css("position","absolute");
    notif.css("top", (($(window).height() - notif.outerHeight()) * 0.9) + $(window).scrollTop() + "px");
    notif.css("left", (($(window).width() - notif.outerWidth()) / 2) + $(window).scrollLeft() + "px");
    notif.delay('fast').fadeOut('slow', function() { notif.remove(); });
}

function skipSong() {
    var postdata = {"jsonrpc": "2.0", "params": {"UID":clientIP}, "id": "bjb7t3bw", "method": "skip"};
    makeRequest(postdata, function(data) 
		{
		    console.log("data:"+data);
		    var output=JSON.parse(data);
		    var result = output["result"];
					 
		    if (result[0]==1) 
			{
			    console.log("Song skipped.");	
			    page=$.mobile.activePage;
			    showNotification(page, "Skip Requested");
			}

		},
	       state.endpoint);

}

function getSupported(callback) {
    if (state.endpoint.length<=0) return;
    var postdata = {"jsonrpc": "2.0", "params": {"UID":clientIP}, "id": "bjb7t3bw", "method": "getsupported"};
    makeRequest(postdata, 
		function(data) 
		{
		    console.log("data:"+data);
		    var output=JSON.parse(data);
		    var result = output["result"];
		    state.supported=result["audio"];
		    state.supported=state.supported.concat(result["video"]);
		    if (callback!==null) callback();
		},
		state.endpoint);

}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function ServerList(domTable)
{
    var table=domTable;
    var list=Array();
    this.edit=function(newserver)
    {
	for (server in list)
	{
	    if (newserver.id===server.id)
	    {
		server=newserver;
		return
	    }
	}
	list.push(newserver);
    }
    this.toString=function()
    {
	JSON.stringify(list);
    }
    this.fromString=function(input)
    {
	list=JSON.parse(input);
    }
    this.redraw = function()
    {
	var html="<ul>";
	for (server in list)
	{
	    html+="<li data-id='"+server.id+"'><a href='/editserver/&id="+server.id+"'>"+server.description+"</a></li>";
	}
	html+="</ul>";
	table.html(html);
    }
    this.getServerFromDom = function(el)
    {
	server = new Server();
	return this.getServerFromID(el.data("id"));
    }
    this.getServerFromID = function(id)
    {
	for (server in list)
	{
	    if (server.id===id) return server;
	}
    }
}

function ServerDetails ()
{
    this.id = -1;
    this.description="";
    this.hostname="";
    this.port=80;
}