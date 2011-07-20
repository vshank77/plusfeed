import re
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.dist import use_library

from django.utils import simplejson as json

from cgi import escape
from datetime import datetime

class MainPage(webapp.RequestHandler):
    
    def get(self):

        res = self.response
        out = res.out

        out.write("""
            <html>
                <head>
                <title>Google Plus Feed</title>
                <style>
                body{
                    font-family: sans-serif;
                    font-size: 14px;
                }
                li{
                    font-size: 11px;
                }
                </style>
                <script type="text/javascript" src="https://apis.google.com/js/plusone.js"></script>
                </head>
                <body>
                    <h1>Unofficial Google+ User Feed</h1>
                    <p>
                    Add the Google+ user number at the end of this URL for their profile feed. Like this: <a href="http://plusfeed.appspot.com/104961845171318028721">http://plusfeed.appspot.com/104961845171318028721</a>.
                    </p>
                    <p>
                    If this site is useful, remember to give it a <g:plusone></g:plusone>
                    </p>
                    <p>
                    Note: The feed will only display *public* items - if none of your posts are public, the feed won't work.
                    </p>
                    <p>
                    You can grab the source for this app here: <a href="https://github.com/russellbeattie/plusfeed">https://github.com/russellbeattie/plusfeed</a>.
                    </p>
                    <p>
                    <em>Originally created by <a href="http://www.russellbeattie.com">Russell Beattie</a></em>
                    </p>
                    """)
        list = memcache.get('list')            
        if list:
            out.write('<p><h3>' + str(len(list)) + ' Google+ profiles currently being served.</h3></p>')
        
        out.write("""
                    <script type="text/javascript">

                      var _gaq = _gaq || [];
                      _gaq.push(['_setAccount', 'UA-24604146-1']);
                      _gaq.push(['_trackPageview']);

                      (function() {
                        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
                        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
                        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
                      })();

                    </script>
                </body>
              </html>
                  """)


class FeedPage(webapp.RequestHandler):
    
    def get(self, p):
    
        res = self.response
        out = res.out
        
        remtags = re.compile(r'<.*?>')
        
        feed = '<?xml version="1.0" encoding="UTF-8"?>\n'
        feed += '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">\n'
        
        HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"
        ATOM_DATE = "%Y-%m-%dT%H:%M:%SZ"

        if 'If-Modified-Since' in self.request.headers:
            try:

                last_seen = datetime.strptime(self.request.headers['If-Modified-Since'], HTTP_DATE_FMT)
                ud = memcache.get('time_' + p)
                if ud and last_seen and ud <= last_seen:
                    logging.info('returning 304')
                    res.set_status(304)
                    return
            except:
                test = 1
        
        #logging.info(self.request.headers)
            
        op = memcache.get(p)
        if op is not None:
            logging.info('delivering from cache')
            res.headers['Content-Type'] = 'application/atom+xml'
            out.write(op)
            return
    
        try:
            logging.info('re-requesting feed')
            url = 'https://plus.google.com/_/stream/getactivities/' + p + '/?sp=[1,2,"' + p + '",null,null,null,null,"social.google.com",[]]'
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                regex = re.compile(',,',re.M)
                txt = result.content
                txt = txt[5:]
                txt = regex.sub(',null,',txt)
                txt = regex.sub(',null,',txt)
                txt = txt.replace('[,','[null,')
                txt = txt.replace(',]',',null]')
                obj = json.loads(txt)
                
                posts = obj[1][0]

                if not posts:
                    self.error(400)
                    out.write('<h1>400 - No Public Items Found</h1>')
                    return


                author = posts[0][3]
                updated = datetime.fromtimestamp(float(posts[0][5])/1000)
                
                feed += '<title>Google Plus User Feed - ' + author + '</title>\n'
                feed += '<link href="https://plus.google.com/' + p + '" rel="alternate"></link>\n'
                feed += '<link href="http://plusfeed.appspot.com/' + p + '" rel="self"></link>\n'
                feed += '<id>https://plus.google.com/' + p + '</id>\n'
                feed += '<updated>' + updated.strftime(ATOM_DATE) + '</updated>\n'
                feed += '<author><name>' + author + '</name></author>\n'
                
                count = 0
                
                for post in posts:
                    #logging.info('post ' + post[21])
                    
                    count = count + 1
                    if count > 10:
                        break
                    
                    
                    dt = datetime.fromtimestamp(float(post[5])/1000)
                    id = post[21]
                    permalink = "https://plus.google.com/" + post[21]
                    
                    desc = ''
                    
                    if post[47]:
                        desc = post[47]                    
                    elif post[4]:
                        desc = post[4]

                    if post[44]:
                        desc = desc + ' <br/><br/><a href="https://plus.google.com/' + post[44][1] + '">' + post[44][0] + '</a> originally shared this post: ';
                    
                    if post[66]:
                        
                        if post[66][0][1]:                        
                            desc = desc + ' <br/><br/><a href="' + post[66][0][1] + '">' + post[66][0][3] + '</a>'

                        if post[66][0][6]:
                            if post[66][0][6][0][1].find('image') > -1:
                                desc = desc + ' <p><img src="http:' + post[66][0][6][0][2] + '"/></p>'
                            else:
                                try:
                                    desc = desc + ' <a href="' + post[66][0][6][0][8] + '">' + post[66][0][6][0][8] + '</a>'
                                except:
                                    test = 1
                    
                    if desc == '':
                        desc = permalink                    
                    
                    
                    ptitle = htmldecode(desc)
                    ptitle = remtags.sub('', ptitle)
                    

                    feed += '<entry>\n'
                    feed += '<title>' + ptitle[:75] + '</title>\n'
                    feed += '<link href="' + permalink + '" rel="alternate"></link>\n'
                    feed += '<updated>' + dt.strftime(ATOM_DATE) + '</updated>\n'
                    feed += '<id>tag:plus.google.com,' + dt.strftime('%Y-%m-%d') + ':/' + id + '/</id>\n'
                    feed += '<summary type="html">' + escape(desc) + '</summary>\n'
                    feed += '</entry>\n'
                    
                  
                feed += '</feed>\n'
                
                output = feed;
                
                memcache.set(p, output, 10 * 60)
                memcache.set('time_' + p, updated)
                
                list = {}
                mlist = memcache.get('list')
                
                if mlist:
                    for k,v in mlist.iteritems():
                        list[k] = v
                
                list[p] = author
                memcache.set('list', list)
                
                
                res.headers['Last-Modified'] = updated.strftime(HTTP_DATE_FMT)
                res.headers['Content-Type'] = 'application/atom+xml'
                #res.headers['Content-Type'] = 'text/plain'
                out.write(output)

            
            else:
                self.error(404)
                out.write('<h1>404 Not Found</h1>')
        
        except Exception, err:
            self.error(500)
            out.write('<h1>500 Server Error</h1><p>' + str(err) + '</p>')



def date_internet(date):
    d = date.strftime('%Y-%m-%dT%H:%M:%S%z')
    return d[:-2] + ':' + d[-2:]

from htmlentitydefs import name2codepoint 
def htmldecode(text):
        """Decode HTML entities in the given text."""
        if type(text) is unicode:
                uchr = unichr
        else:
                uchr = lambda value: value > 255 and unichr(value) or chr(value)
        def entitydecode(match, uchr=uchr):
                entity = match.group(1)
                if entity.startswith('#x'):
                        return uchr(int(entity[2:], 16))
                elif entity.startswith('#'):
                        return uchr(int(entity[1:]))
                elif entity in name2codepoint:
                        return uchr(name2codepoint[entity])
                else:
                        return match.group(0)
        charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
        return charrefpat.sub(entitydecode, text)


application = webapp.WSGIApplication([('/', MainPage), (r'/(.+)', FeedPage)],debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
