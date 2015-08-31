import site
import os

sSitePath = os.path.dirname(__file__)
print "adding python site: '{}'".format(sSitePath) 
site.addsitedir(sSitePath)