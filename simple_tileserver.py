#!/usr/bin/python
#
# Simple live tile server for style development
#
# (c) 2013 dink-straycat <dink.straycat@gmail.com>
#
# original written by
# (c) 2012 Sven Geggus <sven-osm@geggus.net>
#
# Do not use for for production tileservers, 
# use mod_tile + Tirex or renderd instead
#
# Released under the terms of the
# GNU Affero General Public License (AGPL)
# http://www.gnu.org/licenses/agpl-3.0.html
# Version 3.0 or later
#

import math,sys,re,os,ConfigParser
import mapnik


def TileToMeters(tx, ty, zoom):
  initialResolution = 20037508.342789244 * 2.0 / 256.0
  originShift = 20037508.342789244
  tileSize = 256.0
  zoom2 = (2.0**zoom)
  res = initialResolution / zoom2
  mx = (res*tileSize*(tx+1))-originShift
  my = (res*tileSize*(zoom2-ty))-originShift
  return mx, my

def TileToBBox(x,y,z):
  x1,y1=TileToMeters(x-1,y+1,z)
  x2,y2=TileToMeters(x,y,z) 
  return x1,y1,x2,y2

# generate error page if invalid URL has been called  
def InvalidURL(start_response,msg,status):
  html="<html><body>%s</body></html>" % msg
  response_headers = [('Content-type', 'text/html'),('Content-Length', str(len(html)))]
  start_response(status, response_headers)
  return html
 
# generate slyypy map for all styles or a single style
def genSlippyMap(start_response):
  status = '200 OK'
  templ = open(map_template,'r')
  tdata = templ.read()
  templ.close()
  response_headers = [('Content-type', 'text/html'),('Content-Length', str(len(tdata)))]
  start_response(status, response_headers)
  return tdata
 
def showStaticContent(start_response, pathinfo):
  status = '200 OK'
  content = open('static/'+pathinfo,'r')
  tdata = content.read()
  content.close()
  import mimetypes
  response_headers = [('Content-type', mimetypes.guess_type(pathinfo)[0]),('Content-Length', str(len(tdata)))]
  start_response(status, response_headers)
  return tdata

# read configuration if exists
def config_get(config, section, option, default):
  if config.has_option(section,option):
    return config.get(section,option)
  else:
    return default

def application(env, start_response):
  global stylename
  global map_template
  
  status = '200 OK'
  
  pathinfo=env['PATH_INFO']

  # read configuration file  
  config = ConfigParser.ConfigParser()
  cfgfile="tileserver.conf"
  config.read(cfgfile)
  stylename = config_get(config,"global","stylename","osm.xml")
  styledir = config_get(config,"global","styledir","../mapnik-stylesheets")
  map_template = config_get(config,"global","map_template","map_template_leaflet.html")
  
  # show static content when URL starts with '/static/'
  m = re.match(r"^/static/(.+)$", pathinfo)
  if m:
    return showStaticContent(start_response, m.group(1))

  # mod-wsgi gives control to our script only for /name and /name/...
  # thus any length <2 should show the overview page
  if len(pathinfo) < 2:
    return genSlippyMap(start_response)
  
  m = re.match(r"^/tiles/([0-9]+)/+([0-9]+)/+([0-9]+).png$", pathinfo)
  if m is None:
    msg="Invalid URL: %s<br />should be /tiles/&lt;z&gt;/&lt;x&gt;/&lt;y&gt;.png" % pathinfo
    return InvalidURL(start_response,msg,'404 Invalid URL')
    
  z=int(m.group(1))
  x=int(m.group(2))
  y=int(m.group(3))
  
  # check for mapnik style file in requested sandbox
  import os.path
  mapfile=os.path.join(styledir,stylename)
  if not os.path.exists(mapfile):
    msg="ERROR: stylename &gt;%s&lt; does not exist!!!" % stylename
    return InvalidURL(start_response,msg,'404 Invalid sandbox')
  
  # we have a valid Tile-URL request so just render the tile now
  m = mapnik.Map(256, 256)
  mapnik.load_map(m, mapfile)
  bba=TileToBBox(x,y,z)
  bbox=mapnik.Box2d(bba[0],bba[1],bba[2],bba[3])
  m.zoom_to_box(bbox)
  im = mapnik.Image(256, 256)
  mapnik.render(m, im)
  
  output = im.tostring('png')
  
  response_headers = [('Content-type', 'image/png'),
                      ('Content-Length', str(len(output)))]
  start_response(status, response_headers)
  return [output]


if __name__ == "__main__":
  from wsgiref import simple_server
  print "starting service on port 8080."
  sv = simple_server.make_server("", 8080, application)
  sv.serve_forever()
