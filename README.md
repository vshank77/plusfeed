# PlusFeed

Google AppEngine Python code to provide Atom feeds from Google+ profile pages.

***
### Description

Want a **feed** for your Google+ posts?

Simply add a Google+ user number to the end of this site's URL to get
an Atom feed of **public** posts.

Example: http://plusfeed.appspot.com/104961845171318028721

***
### Instructions

Deploy this same code to your own AppEngine instance or run it on your
server with the dev_appserver.py application.

Pull down the Google App Engine SDK for for Python from 
[here](http://code.google.com/appengine/downloads.html).

<pre>
$ /dev/google_appengine/dev_appserver.py -p 8080 /dev/github.com/plusfeed
</pre>

Then use [http://localhost:8080/](http://localhost:8080/) to access
your own instance of PlusFeed.

<pre>
$ curl http://localhost:8080/104961845171318028721
</pre>

***
#### Other projects that parse Google+

Java: http://code.google.com/p/javaplus/

PHP: http://github.com/jmstriegel/php.googleplusapi

***
Created by <a href="http://www.russellbeattie.com">Russell Beattie</a>.

Licensed under the MIT License.
