#!/usr/bin/python
# (c)2uk3y, December 8, 2015
# Greetz to: TioEuy & Bosen

import xbmc,xbmcplugin
import xbmcgui
import sys
import urllib, urllib2
import time
import re, base64
from htmlentitydefs import name2codepoint as n2cp
import httplib
import urlparse
from os import path, system
import socket
from urllib2 import Request, URLError, urlopen
from urlparse import parse_qs
from urllib import unquote_plus
import xbmcaddon
import json
import xbmcvfs
import os

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

pass#print  "Here in default-py sys.argv =", sys.argv

mainURL="http://123movies.to"
thisPlugin = int(sys.argv[1])

addon = xbmcaddon.Addon()
path = addon.getAddonInfo('path')
pic = path+"/icon.png"
picNext = path+"/next.png"
picFanart = path+"/fanart.jpg"
progress = xbmcgui.DialogProgress()
addonInfo = xbmcaddon.Addon().getAddonInfo
makeFile = xbmcvfs.mkdir
dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
favouritesFile = os.path.join(dataPath, 'favourites.db')
metacacheFile = os.path.join(dataPath, 'meta.db')

metaSet = addon.getSetting('enable-meta')
autoView = addon.getSetting('auto-view')
autoViewValue = addon.getSetting('auto-view-value')
autoSubtitle = addon.getSetting('auto-subtitle')


     
Host = "http://123movies.to"
movieHost = Host+"/movie/filter"
infoLink = 'http://123movies.to/movie/loadinfo/'

def getUrl(url, referer=''):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    # req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:43.0) Gecko/20100101 Firefox/43.0')
    if referer:
      req.add_header('Referer', referer)
    response = urllib2.urlopen(req, timeout=5)
    link = response.read()
    response.close()
    return link
    
def playVideo(url, name, pic, subtitle=''):
    title = name
    player = xbmc.Player()
    try:
        xlistitem = xbmcgui.ListItem( title, iconImage=pic, thumbnailImage=pic, path=url)
    except:
        xlistitem = xbmcgui.ListItem( title, iconImage=pic, thumbnailImage=pic )
    
    if autoSubtitle == 'true' and subtitle:
      # if subtitle:
      sub = [subtitle]
      xlistitem.setSubtitles(sub)

    xlistitem.setInfo( "video", { "Title": title } )
    player.play(url,xlistitem)

def gedebug(strTxt):
    print '##################################################################################################'
    print '### GEDEBUG: ' + str(strTxt)
    print '##################################################################################################'
    return
    
def addSearch():
    searchStr = ''
    keyboard = xbmc.Keyboard(searchStr, 'Search')
    keyboard.doModal()
    if (keyboard.isConfirmed()==False):
      return
    searchStr=keyboard.getText()
    if len(searchStr) == 0:
      return
    else:
      return searchStr 

def showSearch():
    stext = addSearch()
    name = stext
    try:
      url = Host + "/movie/search/" + stext.replace(' ','%20')
      ok = showMovieList(search=url)
    except:
      pass

def setContainerView(value=502):
    if autoView == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % str(value) )

def showMainMenu():
    addDirectoryItem("Featured", {
      "name":"Featured", "url":Host, "mode":1, "section":"movie-featured"
      }, pic)
    addDirectoryItem("Movies", {
      "name":"Movies", "url":Host, "mode":4, "section":"movie"
      }, pic)
    addDirectoryItem("TV-Series", {
      "name":"TV-Series", "url":Host, "mode":4, "section":"series"
      }, pic)
    addDirectoryItem("Latest Movies", {
      "name":"Latest Movies", "url":Host, "mode":1, "section":"mlw-latestmovie"
      }, pic)
    addDirectoryItem("Latest TV-Series", {
      "name":"Latest TV-Series", "url":Host, "mode":1, "section":"mlw-featured"
      }, pic)
    addDirectoryItem("Requested", {
      "name":"Requested", "url":Host, "mode":1, "section":"mlw-requested"
      }, pic)
    addDirectoryItem("Top Viewed Today", {
      "name":"Top Viewed Today", "url":Host, "mode":1, "section":"topview-today"
      }, pic)
    addDirectoryItem("Most Favourite", {
      "name":"Most Favourite", "url":Host, "mode":1, "section":"top-favorite"
      }, pic)
    addDirectoryItem("Top Rating", {
      "name":"Top Rating", "url":Host, "mode":1, "section":"top-rating"
      }, pic)
    addDirectoryItem("Top IMDb", {
      "name":"Top IMDb", "url":Host, "mode":1, 'imdb':'topimdb'
      }, pic)
    addDirectoryItem("[COLOR FF00FFFF]My Favourites[/COLOR]", {
      "name":"My Favourites", "url":Host, "mode":5
      }, pic)    
    addDirectoryItem("[COLOR FF00FFFF]Search[/COLOR]", {"name":"Search", "url":Host, "mode":99}, pic)

    setContainerView()
    
    xbmcplugin.endOfDirectory(thisPlugin)

def showFilterMenu(section):
    addDirectoryItem("Most Viewed", {
      "name":"Most Viewed", "url":Host, "mode":1, "section":section, "sortby":"view"
      }, pic)
    addDirectoryItem("Most Favourite", {
      "name":"Most Favourite", "url":Host, "mode":1, "section":section, "sortby":"favorite"
      }, pic)
    addDirectoryItem("Top Rating", {
      "name":"Top Rating", "url":Host, "mode":1, "section":section, "sortby":"rating"
      }, pic)
    addDirectoryItem("Genre", {"name":"Genre", "url":Host, "mode":41, "section":section, "filters":"genre"}, pic)
    addDirectoryItem("Country", {"name":"Country", "url":Host, "mode":41, "section":section, "filters":"country"}, pic)
    addDirectoryItem("Year", {"name":"Year", "url":Host, "mode":41, "section":section, "filters":"year"}, pic)

    setContainerView()

    xbmcplugin.endOfDirectory(thisPlugin)

def showFilterList(section, filters):
    url = movieHost+'/'+section

    if filters == 'genre':
      lister = getGenre(url)
    elif filters == 'country':
      lister = getCountry(url)
    elif filters == 'year':
      lister = getYear(url)

    for value,title in lister:
      title = re.sub(r"\s$", '', title)
      addDirectoryItem(title, {"name":title, "url":Host, "mode":1, "section":section, "sortby":"all", filters:value}, pic)

    if filters == 'year':
      title = "Older"
      value = "older-2011"
      addDirectoryItem(title, {"name":title, "url":Host, "mode":1, "section":section, "sortby":"all", filters:value}, pic)

    setContainerView()

    xbmcplugin.endOfDirectory(thisPlugin)

def getGenre(url):
    content = getUrl(url)

    regEx = 'value="(.+?)".*?name="genres\[\]"\n*\s*.*>(.+?)</label>'
    match = re.compile(regEx).findall(content)
    return match

def getCountry(url):
    content = getUrl(url)

    regEx = 'value="(.+?)".*?name="countries\[\]"\n*\s*.*>(.+?)</label>'
    match = re.compile(regEx).findall(content)
    return match

def getYear(url):
    content = getUrl(url)

    regEx = 'value="(.+?)".*?name="year"\n*\s*.*>(.+?)</label>'
    match = re.compile(regEx).findall(content)
    return match

def showMovieList(section='all', sortby='latest', genre='all', country='all', year='all', other='all', unknown='all', page='', search='', imdb=''):
    url = movieHost + '/' + section + '/' + sortby + '/' + genre + '/' + country + '/' + year + '/' + other + '/' + unknown + '/' + page
    # gedebug(url)
    search = search.replace('%3a',':').replace('%2f','/')

    if not page: page = 1

    if search:
      url = search + '/' + str(page)

    if imdb:
      url = mainURL+'/movie/'+imdb + '/' + str(page)

    if section == 'movie-featured' or section == 'mlw-latestmovie' or section == 'mlw-featured' or section == 'mlw-requested':
      url = Host

    if section == 'topview-today' or section == 'top-favorite' or section == 'top-rating':
      url = mainURL+'/site/ajaxContentBox/'+section

    content = getUrl(url)

    if section == 'movie-featured' or section == 'mlw-latestmovie' or section == 'mlw-featured' or section == 'mlw-requested':
      regEx = '<.*'+section+'.*?\n\s*(.+?)<scrip'
      content = re.compile(regEx, re.DOTALL).findall(content)[0]

    if section == 'topview-today' or section == 'top-favorite' or section == 'top-rating':
      data = json.loads(content)
      content = data['content']

    regEx = '<.*ml-item.*\n*\s*<a href="(.+?)"\n*\s*data-url="(.+?)".*\n*\s*.*\n*\s*title="(.+?)".*\n*\s*(<.).*\n*\s*.*data-original="(.+?)"'
    match = re.compile(regEx).findall(content)

    part = 'files'
    for url,info,title,mode,pic in match:

      if mode == '<s':
        mode = 3
        part = 'tvshows'
        media_type = 'tv'
        txtInfo = 'TV Show Information'
      else:
        mode = 2
        part = 'movies'
        media_type = 'movie'
        txtInfo = 'Movie Information'

      if metaSet == 'true':
        metaData = getMeta(url)
      else:
        metaData = {}
        id = re.compile('film\/(.+?)\/').findall(url)[0] 
        metaData['id'] = id
        metaData['link'] = url
        metaData['title'] = title
        metaData['year'] = ''

      metaData['mode'] = mode
      metaData['txtinfo'] = txtInfo
      metaData['part'] = part
      metaData['media_type'] = media_type
      metaData['thumbnail'] = pic

      addon_handle = int(sys.argv[1])
      try:
        xbmcplugin.setContent(addon_handle, metaData['part'])
      except:
        xbmcplugin.setContent(addon_handle, 'files')

      title = re.sub(r'\s\(\d{4}\)','',title)
      if metaData['year']:
        title1 = title + ' ('+str(metaData['year'])+')'
      else:
        title1 = title
        
      addDirectoryItem(title1, {"name":title, "url":url, "mode":mode}, pic, metaData)

    try:
      pagination = re.compile('<ul class="pagination">').findall(content)[0]

      pageNext = int(page)+1

      urlNext = movieHost + '/' + section + '/' + sortby + '/' + genre + '/' + country + '/' + year + '/' + other + '/' + str(pageNext)

      if search:
        urlNext = search + '/' + str(pageNext)

        addDirectoryItem("[I]Next Page[/I]", {
          "name":"Next Page", "url":urlNext, "mode":1, "page":pageNext, "search":search
          }, picNext)
      elif imdb:
        urlNext = mainURL+'/movie/'+imdb + '/' + str(pageNext)

        addDirectoryItem("[I]Next Page[/I]", {
          "name":"Next Page", "url":urlNext, "mode":1, "page":pageNext, "imdb":imdb
          }, picNext)
      elif section == 'movie-featured' or section == 'mlw-latestmovie' or section == 'mlw-featured' or section == 'topview-today' or section == 'top-favorite' or section == 'top-rating' or section == 'mlw-requested':
        pass
      else:
        addDirectoryItem("[I]Next Page[/I]", {
            "name":"Next Page", "url":urlNext, "mode":1, "section":section, "sortby":sortby, "genre":genre, "country":country, "year":year, "other":other, "page":pageNext, "search":search
            }, picNext)
    except:
      pass

    setContainerView(autoViewValue)

    xbmcplugin.endOfDirectory(thisPlugin)


def getMeta(url):
    id = re.compile('film\/(.+?)\/').findall(url)[0] 

    content = getUrl(url)

    title = re.compile('<meta property="og:title" content="(.+?)"/>').findall(content)[0]

    try:# get Plot
      plot = re.compile('div\sclass="desc">\n\s*(.+?)[\n|<]').findall(content)[0]
    except:plot = ''
    try:# get Release year
      year = re.compile('Release:.*\s(\d{4})</p>').findall(content)[0]
      # year = int(year)
      year = int(year)
    except:year = ''
    try:# get fanart
      fanart = re.compile('background-image:\surl\((.+?)\)').findall(content)[0]
    except:fanart = ''
    try:# get Genre
      genres = re.compile('<p>\n\s*.*Genre:.*\s\n*\s*(.+?)</p>').findall(content)[0]
      genres = re.compile('">(.+?)</',re.DOTALL).findall(genres)
      genre = ' / '.join(genres)
    except:genre = ''
    try:# get Actor
      actors = re.compile('<p>\n\s*.*Actor:.*\s\n*\s*(.+?)</p>').findall(content)[0]
      actors = re.compile('">(.+?)</',re.DOTALL).findall(actors)
    # actors = ','.join(actors)
      # gedebug(actors)
    except:actors = []
    try:# get Director
      director = re.compile('Director:.*\s\n*\s*.*">(.+?)</a>').findall(content)[0]
    except:director = ''
    try:# get Country
      country = re.compile('Country:.*\s\n*\s*.*">(.+?)</a>').findall(content)[0]
    except:country = ''
    try:# get Duration
      duration = re.compile('Duration:.*\s(\d.+?)\smin</p>').findall(content)[0]
      duration = int(duration)*60
    except:duration = 0
    try:# get Quality
      quality = re.compile('Quality:.*\s<.*>(.+?)</.*></p>').findall(content)[0]
    except:quality = ''
    try:# get IMDb
      imdb = re.compile('IMDb:.*\s(.+?)</p>').findall(content)[0]
    except:imdb = ''    
    try:# get total episode
      episode = re.compile('Episode:.*\s(\d{1,2})\seps</').findall(content)[0]
      episode = int(episode)
    except:episode = ''

    link = url

    meta = {
      'link':link,
      'title':title,
      'id':id,
      'plot':plot,
      'year':year,
      'fanart':fanart,
      'genre':genre,
      'cast':actors,
      'director':director,
      'country':country,
      'duration':duration,
      'quality':quality,
      'rating':imdb,
      'episode':episode,
    }
    return meta

def showMovieLink(url, name, library='false'):
    url = url+'watching.html'
    content = getUrl(url)

    # regEx = '<.*movie-id="(.+?)"'
    regEx = '<.*player-token="(.+?)".*?movie-id="(.+?)"'
    data = re.compile(regEx, re.DOTALL).findall(content)[0]
    movieID = data[1]
    movieToken = data[0]
    server = '9'

    # get thumbnail
    regEx = '<meta property="og:image" content="(.+?)"/>'
    pic = re.compile(regEx).findall(content)[0]
    # get Release year
    year = re.compile('Release:.*\s(\d{4})</p>').findall(content)[0]
    
    # progress bar 
    progress.create('Progress', 'Please wait while we grab all source.')

    data = []
    try: #search server
      name = name+' '+year 
      content = getUrl(mainURL+'/movie/loadepisodes/'+movieID)
      regEx = 'id="server-(.+?)"'
      match = re.compile(regEx).findall(content)

      regEx = 'hash="(.+?)".*\n.*episode-id="(.+?)".*\n.*\n.*\n.*>(.+?)</'
      match = re.compile(regEx).findall(content)

      if len(match) > 1:
        i = 0
        l = len(match)
        intl = str(l)+'.0'

        for hashCode, videoID, quality in match:
          # progess bar update
          updateProgressBar(i, l, intl)
          if progress.iscanceled():
            progress.close()
            break
          i = i + 1
          server = str(i)
          if library == 'true':
            data.extend(getQuality(name, videoID, server, pic, quality=quality, library='true', hashCode=hashCode))
          else:
            getQuality(name, videoID, server, pic, quality=quality, hashCode=hashCode)

      else:
        server = '1'
        hashCode = match[0][1]
        videoID = match[0][2]
        if library == 'true':
          data.append(getQuality(name, videoID, server, pic, quality=quality, library='true', hashCode=hashCode))
        else:
          getQuality(name, videoID, server, pic, quality=quality, hashCode=hashCode)
    except:
      pass

    progress.close()
    if library == 'true':
      return data
    else:
      setContainerView()
      xbmcplugin.endOfDirectory(thisPlugin)

def showEpisodeMenu(url, name):
    url = url+'watching.html'
    content = getUrl(url)
    # get thumbnail
    regEx = '<meta property="og:image" content="(.+?)"/>'
    pic = re.compile(regEx).findall(content)[0]

    regEx = '<.*player-token="(.+?)".*?movie-id="(.+?)"'
    data = re.compile(regEx, re.DOTALL).findall(content)[0]
    # movieID = re.compile(regEx, re.DOTALL).findall(content)[0]
    movieID = data[1]
    movieToken = data[0]
    server = '9'
    episodes = getEpisode(movieID, movieToken)
    # movieToken = ''

    for episode in episodes:
      addDirectoryItem(episode, {"name":episode, "url":url, "mode":31, 'mvID':movieID, 'mvToken':movieToken, 'thumbnail':pic, 'tvTitle':name}, pic)

    xbmcplugin.endOfDirectory(thisPlugin)

def showEpisodeLink(name, mvID, mvToken, epName, thumbnail='', library='false'):
    movieID = mvID
    movieToken = mvToken
    pic = thumbnail
    name = urllib.unquote(name)
    # progress bar create
    progress.create('Progress', 'Please wait while we grab all source.')
    # if movieID:
    try: #search server
      content = getUrl(mainURL+'/ajax/get_episodes/'+movieID+'/'+movieToken)
      epName = urllib.unquote(epName)
      regEx = 'Ep.*\s(\d{1,2})|:\s'
      epNum = re.compile(regEx).findall(epName)[0]

      regEx = '"Ep(?:\w+\s|\s|\.\s)('+epNum+'[":]).*?hash="(.+?)"\n\s*.*?episode-id="(.+?)"'
      match = re.compile(regEx, re.DOTALL).findall(content)

      data = []
      if len(match) > 1:
        i = 0
        l = len(match)
        intl = str(l)+'.0'

        for server, hashCode, videoID in match:
          # progess bar update
          updateProgressBar(i, l, intl)
          if progress.iscanceled():
            progress.close()
            break
          i = i + 1
          server = str(i)
          try:
            if library == 'true':
              data.extend(getQuality(name, videoID, server, pic, epName, library='true', hashCode=hashCode))
            else:
              getQuality(name, videoID, server, pic, epName, hashCode=hashCode)
          except: pass
      else:
        server = '1'
        hashCode = match[0][1]
        videoID = match[0][2]
        try:
          if library == 'true':
            data.extend(getQuality(name, videoID, server, pic, epName, library='true', hashCode=hashCode))
          else:
            getQuality(name, videoID, server, pic, epName, hashCode=hashCode)
        except: pass
    except:
      pass

    progress.close()
    if library == 'true':
      return data

    setContainerView(autoViewValue)
    xbmcplugin.endOfDirectory(thisPlugin)

def updateProgressBar(i, l, intl):
    percent = int( ( i / float(intl) ) * 100)
    message = "Checking Available Server : " + str(i) + " out of "+str(l)
    progress.update( percent, "", message, "" )
    xbmc.sleep( 1000 )

def getEpisode(movieID, movieToken):
    content = getUrl(mainURL+'/ajax/get_episodes/'+movieID+'/'+movieToken)
    #search episode
    try:
      regEx = 'Server\s9\s*..\w*.\s*..\w*.\n\s*.\w*\s\w*="les-content">\n*\s*(.*?)\n*\s*</div>'
      match = re.compile(regEx, re.DOTALL).findall(content)[0]
    except:
      for x in xrange(1,10):
        try:
          regEx = 'Server\s'+str(x)+'\s*..\w*.\s*..\w*.\n\s*.\w*\s\w*="les-content">\n*\s*(.*?)\n*\s*</div>'
          match = re.compile(regEx, re.DOTALL).findall(content)[0]
          break
        except: pass
    # search title
    regEx = 'title="(.*?)"'
    match = re.compile(regEx).findall(match)

    return match

def showQuality(name, url, episode='false'):
  playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
  playlist.clear()
  resolve = xbmcplugin.setResolvedUrl
  item = xbmcgui.ListItem
  resolve(int(sys.argv[1]), True, item(path=''))
  execute = xbmc.executebuiltin
  execute('Dialog.Close(okdialog)')
  # window = xbmcgui.Window(10000)
  # gedebug(window.getProperty('PseudoTVRunning'))
  # if window.getProperty('PseudoTVRunning') == 'True':
  #   sourcesDirect() 
  try:
    if episode == 'false':
      quality = showMovieLink(url, name, 'true')
    elif episode == 'true':
      mvID, mvToken, epName = url[0], url[1], url[2]
      quality = showEpisodeLink(name, mvID, mvToken, epName, '', 'true')

    list = []
    link = []
    thumbnail = []
    vTitle = []
    sub = []
    for data in quality:
      list.append(data['label'])
      link.append(data['url'])
      thumbnail.append(data['thumbnail'])
      vTitle.append(data['vTitle'])
      sub.append(data['subtitle'])
    select = selectDialog(list, name)
    if select == -1: return  

    url = link[select]
    name = vTitle[select]
    pic = thumbnail[select]
    subtitle = sub[select]
    playVideo(url, name, pic, subtitle)

  except:
    infoDialog('No stream available')

def selectDialog(list, heading=addonInfo('name')):
    dialog = xbmcgui.Dialog()
    return dialog.select(heading, list)

def getQuality(name, videoID, server, pic='', epName='', quality='', library='false', hashCode=''):
    url = mainURL + '/ajax/load_episode/' + videoID + '/' + hashCode
    content = getUrl(url)

    if epName:
      regEx = '</title>\n*\s*(.+?)\n*\s*</item>'
      content = re.compile(regEx, re.DOTALL).findall(content)[0]
    else:
      q = quality
      if q == 'TS' or q == 'CAM':
        quality = '  |  ' + q
      else:
        quality = ''

    regEx = 'source\n\s*.*?file="(.*?)"\n\s*label="(.+?)"'
    match = re.compile(regEx).findall(content)
    try:
      regEx = 'track.*\n*\s*file="(.+?)"\n*\s*label=".*"'
      subtitle = re.compile(regEx).findall(content)[0]
    except: subtitle = ''

    data = []
    for url,label in match:
      regEx = '=m(.+)'
      match = re.compile(regEx).findall(url)[0]

      if match == '18': label = 'SD'
      elif match == '22': label = 'HD'
      elif match == '37': label = '1080p'
      else: label = 'SD'
      title = 'Server '+ server + '  |  ' + label + quality

      name = urllib.unquote(urllib.unquote(name))
      
      try:
        sNum = re.compile('Season\s(.+?)').findall(name)[0]
        sNum = 'S'+str(sNum.zfill(2))
        eNum = re.compile('Ep.*?\s(\d{1,3})|\s|:').findall(epName)[0]
        eNum = 'E'+str(eNum.zfill(2))
        name = re.compile('(.+?) -').findall(name)[0]
        name = urllib.unquote(name)
        name = name.replace(' ','.')
        name = name +'.'+ sNum + eNum
      except:
        name = name.replace(' ','.')
      
      if library == 'true':
        data.append({'url':url, 'label':title, 'thumbnail':pic, "vTitle":name, 'subtitle': subtitle})
      else:
        addDirectoryItem(title, {"name":title, "url":url, "mode":69, "thumbnail":pic, "vTitle":name, 'subtitle': subtitle}, pic)
    
    if library == 'true': return data

def showFavMenu():
    addDirectoryItem("Favourite Movies", {"name":"Favourite Movies", "url":Host, "mode":51, 'fav_type':'movies'}, pic)
    addDirectoryItem("Favourite TV-Series", {"name":"Favourite TV-Series", "url":Host, "mode":51, 'fav_type':'tvshows'}, pic)
    setContainerView()
    xbmcplugin.endOfDirectory(thisPlugin)

def showFavList(fav_type):
  try:
    items = getFavourites(fav_type)
    data = [i[1] for i in items]
    # gedebug(items)
    for i in data:
      if i['year']:
        title = i['title']+' ('+str(i['year'])+')'
      else:
        title = i['title']
      name = i['title']
      pic = i['thumbnail']
      link = i['link']
      mode = i['mode']
      txtinfo = i['txtinfo']
      part = i['part']
      media_type = i['media_type']

      if metaSet == 'true':
        metaData = getMeta(link)
      else:
        metaData = {}
        id = re.compile('film\/(.+?)\/').findall(link)[0] 
        metaData['id'] = id

      metaData['mode'] = mode
      metaData['txtinfo'] = txtinfo
      metaData['part'] = part
      metaData['media_type'] = media_type
      metaData['thumbnail'] = pic

      addon_handle = int(sys.argv[1])
      try:
        xbmcplugin.setContent(addon_handle, metaData['part'])
      except:
        xbmcplugin.setContent(addon_handle, 'files')

      addDirectoryItem(title, {"name":name, "url":link, "mode":mode}, pic, metaData)

  except:
    pass
  
  setContainerView(autoViewValue)
  xbmcplugin.endOfDirectory(thisPlugin)

def getFavourites(content, id=''):
    if id:
      try:
          dbcon = database.connect(favouritesFile)
          dbcur = dbcon.cursor()
          dbcur.execute("SELECT * FROM %s WHERE id = '%s'" % (content,id))
          items = dbcur.fetchall()
      except: items = []
    else:
      try:
          dbcon = database.connect(favouritesFile)
          dbcur = dbcon.cursor()
          dbcur.execute("SELECT * FROM %s" % (content))
          items = dbcur.fetchall()
          items = [(i[0].encode('utf-8'), eval(i[1].encode('utf-8'))) for i in items]
      except: item = []
    return items

def addFavourite(meta, content, query=None):
    try:
        # gedebug(meta)
        item = dict()
        meta = json.loads(meta)
        # gedebug(json.dumps(meta))
        try: id = meta['id']
        except: id = meta['id']

        if 'id' in meta: title = item['id'] = meta['id']
        if 'title' in meta: title = item['title'] = meta['title']
        if 'thumbnail' in meta: thumnbail = item['thumbnail'] = meta['thumbnail']
        if 'year' in meta: item['year'] = meta['year']
        if 'link' in meta: item['link'] = meta['link']
        if 'fanart' in meta: item['fanart'] = meta['fanart']
        if 'mode' in meta: item['mode'] = meta['mode']
        if 'txtinfo' in meta: item['txtinfo'] = meta['txtinfo']
        if 'media_type' in meta: item['media_type'] = meta['media_type']
        if 'part' in meta: item['part'] = meta['part']

        makeFile(dataPath)
        dbcon = database.connect(favouritesFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS %s (""id TEXT, ""items TEXT, ""UNIQUE(id)"");" % content)
        dbcur.execute("DELETE FROM %s WHERE id = '%s'" % (content, id))
        dbcur.execute("INSERT INTO %s Values (?, ?)" % content, (id, repr(item)))
        dbcon.commit()

        if query == None: refresh()
        infoDialog("Added to Favourites", heading=title)
    except:
        return

def deleteFavourite(meta, content):
    try:
        meta = json.loads(meta)
        if 'title' in meta: title = meta['title']

        try:
            dbcon = database.connect(favouritesFile)
            dbcur = dbcon.cursor()
            try: dbcur.execute("DELETE FROM %s WHERE id = '%s'" % (content, meta['id']))
            except: pass
            dbcon.commit()
        except:
            pass

        refresh()
        infoDialog('Removed from Favourites', heading=title)
    except:
        return

def refresh():
    execute = xbmc.executebuiltin
    return execute('Container.Refresh')

def addonIcon():
    addonPath = xbmc.translatePath(addonInfo('path'))
    setting = xbmcaddon.Addon().getSetting
    appearance = setting('appearance').lower()
    if appearance in ['-', '']: return addonInfo('icon')
    else: return os.path.join(addonPath, 'resources', 'media', appearance, 'icon.png')

def infoDialog(message, heading=addonInfo('name'), icon=addonIcon(), time=5000):
    dialog = xbmcgui.Dialog()
    try: dialog.notification(heading, message, icon, time, sound=False)
    except: execute("Notification(%s,%s, %s, %s)" % (heading, message, time, icon))

def addtoLibrary(meta, content):
    condVisibility = xbmc.getCondVisibility
    dupe_setting = 'true'
    check_setting = 'false'
    library_setting = 'true'
    jsonrpc = xbmc.executeJSONRPC
    execute = xbmc.executebuiltin
    infoDialogStat = False

    meta = json.loads(meta)

    name = meta['title']
    title = meta['title']
    year = meta['year']

    if not condVisibility('Window.IsVisible(infodialog)') and not condVisibility('Player.HasVideo'):
      infoDialog('Adding to library...', time=10000000)
      infoDialogStat = True

    try:
      strmFile(json.dumps(meta))
    except:
      pass

    if range == True: return

    if infoDialogStat == True:
      infoDialog('Process Complete', time=1)

    if not condVisibility('Library.IsScanningVideo'):
      execute('UpdateLibrary(video)')

def strmFile(i):
    transPath = xbmc.translatePath
    movies_lib_folder = os.path.join(transPath('special://userdata/addon_data/plugin.video.123movies/Movies'),'')
    tvshows_lib_folder = os.path.join(transPath('special://userdata/addon_data/plugin.video.123movies/TVShows'),'')

    openFile = xbmcvfs.File

    i = json.loads(i)

    try:
      name = title = i['title']
      url = i['link']
      thumbnail = i['thumbnail']
      year = i['year']

      sysname, systitle = urllib.quote_plus(name), urllib.quote_plus(title)

      link = url+'watching.html'
      content = getUrl(link)
      regEx = '<.*movie-id="(.+?)"'
      movieID = re.compile(regEx).findall(content)[0]
      movieToken = ''
      server = '9'

      if i['part'] == 'movies':
        library_folder = movies_lib_folder
        transname = str(name).translate(None, '\/:*?"<>|').strip('.')
        transname = transname+' ('+str(year)+')'
        content = '%s?mode=getQualityMovies&url=%s&vTitle=%s&year=%s&movieID=%s&movieToken=%s&server=%s' % (sys.argv[0], url, systitle, year, movieID, movieToken, server)
        makeFile(library_folder)
        folder = os.path.join(library_folder, transname)
        makeFile(folder)

        stream = os.path.join(folder, transname + '.strm')
        file = openFile(stream, 'w')
        file.write(str(content))
        file.close()
      
      elif i['part'] == 'tvshows':
        library_folder = tvshows_lib_folder
        season = re.compile(r'\s-\sSeason\s(\d{1,3})').findall(name)[0]
        name = re.sub(r'\s-\sSeason\s\d{1,3}','',name)
        transname = str(name).translate(None, '\/:*?"<>|').strip('.')
        transname = transname+' ('+str(year)+')'
        transseason = 'Season %s' % (season)
        makeFile(library_folder)
        folder = os.path.join(library_folder, transname)
        makeFile(folder)
        folder = os.path.join(folder, transseason)
        makeFile(folder)

        episodes = getEpisode(movieID)
        e = 1
        for episode in episodes:
          content = '%s?mode=getQualityTVShows&url=%s&vTitle=%s&year=%s&movieID=%s&movieToken=%s&server=%s&season=%s&episode=%s&epName=%s' % (sys.argv[0], url, systitle, year, movieID, movieToken, server, season, e, episode)
          transepisode =  transname + ' S%sE%s' % (season,e)
          stream = os.path.join(folder, transepisode + '.strm')
          file = openFile(stream, 'w')
          file.write(str(content))
          file.close()
          e = e+1

    except:
      pass

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}  

def addDirectoryItem(name, parameters={},pic="", meta=''):
    li = xbmcgui.ListItem(name, iconImage=pic, thumbnailImage=pic)
    # li = xbmcgui.ListItem(name)
    li.setInfo( "video", { "Title" : name, "FileName" : name} )
    if meta:
      try:
        import HTMLParser
        parser = HTMLParser.HTMLParser()
        meta['plot'] = parser.unescape(meta['plot'])
      except:
        pass

      li.setInfo( "video", meta )
      try:
        pic = meta['fanart']   
      except: pass 
      
      favitems = getFavourites(meta['part'], meta['id'])
      # context menu
      sysmeta = urllib.quote_plus(json.dumps(meta))
      cm = []
      cm.append((meta['txtinfo'], 'Action(Info)'))
      if favitems:
        cm.append(('Delete from Favourites', 'RunPlugin(%s?mode=delfromFavourite&meta=%s&content=%s)' % (sys.argv[0], sysmeta, meta['part'])))
      else:
        cm.append(('Add to Favourites', 'RunPlugin(%s?mode=addtoFavourite&meta=%s&content=%s)' % (sys.argv[0], sysmeta, meta['part'])))
      cm.append(('Add to Library', 'RunPlugin(%s?mode=addtoLibrary&meta=%s&content=%s)' % (sys.argv[0], sysmeta, meta['part'])))
      li.addContextMenuItems(cm, replaceItems=True)
    
    if pic == path+"/icon.png" or pic == path+"/next.png": pic = picFanart
    li.setProperty('Fanart_Image', pic)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    # gedebug(url)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

params = parameters_string_to_dict(sys.argv[2])
name =  str(params.get("name", ""))
url =  str(params.get("url", ""))
url = urllib.unquote(url)
mode =  str(params.get("mode", ""))
section =  str(params.get("section", ""))
sortby =  str(params.get("sortby", "latest"))
genre =  str(params.get("genre", "all"))
country = str(params.get("country", "all"))
year = str(params.get("year", "all"))
other = str(params.get("other", "all"))
unknown = str(params.get("unknown", "all"))
page = str(params.get("page", ""))
mvID = str(params.get("mvID", ""))
mvToken = str(params.get("mvToken", ""))
filters = str(params.get("filters", ""))
search = str(params.get("search", ""))
imdb = str(params.get("imdb", ""))
thumbnail = str(params.get("thumbnail", ""))
thumbnail = urllib.unquote(thumbnail)
tvTitle = str(params.get("tvTitle", ""))
vTitle = str(params.get("vTitle", ""))
fav_type =  str(params.get("fav_type", ""))
subtitle =  str(params.get("subtitle", ""))
subtitle = urllib.unquote(subtitle)

#### ACTIONS ####
if not sys.argv[2]:
    pass#print  "Here in default-py going in showContent"
    ok = showMainMenu()
else:
    if mode == str(1): #Click Latest Movie / TV Series
        ok = showMovieList(section, sortby, genre, country, year, other, unknown, page, search, imdb)
    elif mode == str(2):  #Click Movie Title
        ok = showMovieLink(url, name)
    elif mode == str(3):  #Click TV Series Title
        ok = showEpisodeMenu(url, name)
    elif mode == str(31):  #Click Episode
        ok = showEpisodeLink(tvTitle, mvID, mvToken, name, thumbnail)
    elif mode == str(4):  #Click Drama Other
        ok = showFilterMenu(section)
    elif mode == str(41):  #Click Drama Other
        ok = showFilterList(section, filters) 
    elif mode == str(99):  #Click Search
        ok = showSearch()
    elif mode == str(69): #Play video
        ok = playVideo(url, vTitle, thumbnail, subtitle)
    elif mode == str(5):  #show fav menu
        ok = showFavMenu()        
    elif mode == str(51): #show fav list
        ok = showFavList(fav_type)      
    elif mode == "addtoFavourite": #add to favorites
        params2 = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
        meta =  params2['meta']
        content =  params2['content']
        # gedebug(sys.argv[2])
        ok = addFavourite(meta, content)
    elif mode == "delfromFavourite": #add to favorites
        params2 = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
        meta =  params2['meta']
        content =  params2['content']
        # gedebug(sys.argv[2])
        ok = deleteFavourite(meta, content)
    elif mode == "addtoLibrary": #add to library
        params2 = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
        meta =  params2['meta']
        content =  params2['content']
        ok = addtoLibrary(meta, content)
    elif mode == "getQualityMovies": #add to library
        params2 = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
        name = params2['vTitle']
        url = params2['url']
        movieID =  params2['movieID']
        movieToken =  params2['movieToken']
        server = params2['server']
        ok = showQuality(name, url)
    elif mode == "getQualityTVShows": #add to library
        params2 = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
        name = params2['vTitle']
        url = params2['url']
        movieID =  params2['movieID']
        movieToken =  params2['movieToken']
        server = params2['server']
        season = params2['season']
        episode = params2['episode']
        epName = params2['epName']
        data = [movieID, movieToken, epName]
        ok = showQuality(name, data, 'true' )