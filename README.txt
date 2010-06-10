PubTal 3.4
------------
A template driven web site builder for small sites.

Installation
------------
Full installation instructions for Linux, MacOS X and Windows can be found in documentation/html/installation.html.

To install PubTal under Unix:
  (Note that to perform the installation of PubTal you will probably
   have to have the Python Development package installed.)
  
  1 - Become root
  2 - Run "python setup.py install"
	
Installing Plugins
------------------
PubTal supports the addtion of new functionality through a plugin architecture.
Several plugins are installed by default with PubTal to provide support for
HTMLText, OpenOffice, Catalogue, Binary, and Raw content types.

Additional plugins that are not installed by default can be found in the
optional-plugins directory.  Currently these include:

 textile.py - provides Textile (http://www.textism.com/tools/textile/) 
 support.  This requires pyTextile (http://diveintomark.org/projects/pytextile/)
 and Python 2.2 to be installed.

 abiwordContent - provides AbiWord content support.  AbiWord currently has
 some significant bugs, which is why this plugin is not installed by default.
 
 CSVPlugin - Provides support for generating multiple web pages base on the
 contents of a .CSV file.  Documentation on how to use this plugin is included
 in the main documentation.

To install these extra plugins (or any other PubTal 2.x plugin) simply copy
 the plugin to the location of the PubTal plugin directory, beneath the Python 
site-packages directory.

(Under Debian this is can be found in: 
/usr/lib/python2.2/site-packages/pubtal/plugins/)

Alternative add the following configuration option to your site configuration
file, replacing /usr/local/PubTal/plugins/ with the path to the plugin dir:

<SiteConfig>
additional-plugins-dir /usr/local/PubTal/plugins/
</SiteConfig>


The Commands
------------
PubTal has one command used to build a site's HTML pages, and one to upload 
generated pages.

The command for generating a site is: updateSite.py configFile

To upload a site use the uploadSite.py command, details of which can be found 
in the documentation.
	
Getting Started
---------------
Documentation for PubTal can be found in the documentation/html/
directory.  

Additionally there are several example websites included for experimentation
under the examples directory.  A very straight forward example is 
in examples/homepage/ and a more complicated example demonstrating 
macros is in examples/macro-example/

Migrating between PubTal 2.x and 3.0
------------------------------------
All 2.x PubTal sites should work, without any changes, in the 3.x series.

Any custom written plugins for 2.x will need to be updated to reflect internal
API changes.  
