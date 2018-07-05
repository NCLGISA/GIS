#!/usr/bin/env python2
# FacilitiesGeocoder.py
# City of Raleigh IT Dept - Peter Sherman
# Rebuilds address locator and publishes to ArcGIS Server

print "starting script"

import arcpy
import pprint
from datetime import datetime
import xml.dom.minidom as DOM
import smtplib

# overwrite feature classes already created
arcpy.env.workspace = "<path to scratch fgdb>"
arcpy.env.overwriteOutput = True

# rebuild locator
print "rebuilding locator"
arcpy.RebuildAddressLocator_geocoding("\\\\<path to address locator>\Addresses_Locator_Wake\MAR_Wake_Addresses")
# http://enterprise.arcgis.com/en/server/10.3/administer/linux/scripting-service-publishing-with-arcpy.htm
# http://enterprise.arcgis.com/en/server/10.3/administer/linux/scripting-with-the-arcgis-rest-api.htm

# initialize errorCounter to count successful publishes
errorCounter = 0

# publish to prd 3
locator_path = "//<path to address locator>/Addresses_Locator_Wake/MAR_Wake_Addresses"
sddraft_file = "//<path to address locator>/Addresses_Locator_Wake/FacilitiesGeo.sddraft"
sd_file = "//<path to address locator>/Addresses_Locator_Wake/MAR_Wake_Geocoder.sd"
service_name = "MAR_Wake_Geocoder"
summary = "Address locator for Facilities and Ops"
tags = "address, locator, geocode"
gis_server_connection_file = "//<path to address locator>/Addresses_Locator_Wake/<.ags connection file to arcgis server>"

# Create the sd draft file
analyze_messages  = arcpy.CreateGeocodeSDDraft(locator_path, sddraft_file, service_name,
                           connection_file_path=gis_server_connection_file,
                           summary=summary, tags=tags, max_result_size=20,
                           max_batch_size=500, suggested_batch_size=150)
#edit XML to allow overwrite of service draft
newType = 'esriServiceDefinitionType_Replacement'
xml = sddraft_file
doc = DOM.parse(xml)
descriptions = doc.getElementsByTagName('Type')
for desc in descriptions:
    if desc.parentNode.tagName == 'SVCManifest':
        if desc.hasChildNodes():
            desc.firstChild.data = newType
outXml = xml    
f = open(outXml, 'w')     
doc.writexml( f )     
f.close()

# Stage and upload the service if the sddraft analysis did not contain errors
if analyze_messages['errors'] == {}:
    try:
        # Execute StageService to convert sddraft file to a service definition (sd) file 
        arcpy.server.StageService(sddraft_file, sd_file)

        # Execute UploadServiceDefinition to publish the service definition file as a service
        arcpy.server.UploadServiceDefinition(sd_file, gis_server_connection_file, service_name, "")
        print("The geocode service was successfully published")
    except arcpy.ExecuteError:
        print("An error occurred")
        print(arcpy.GetMessages(2))
        errorCounter += 1
else: 
    # If the sddraft analysis contained errors, display them
    print("Error were returned when creating service definition draft")
    pprint.pprint(analyze_messages['errors'], indent=2)
    errorCounter += 1

# Email results (success/fail)
fromaddr = 'from email address'
toaddrs  = 'to email address'
username = ''
password = ''
server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()
server.login(username,password)

if errorCounter >= 1:
    msg = 'Geocode publish error: ' + str(errorCounter)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
else:
    msg = 'Geocode completed successfully ' + str(errorCounter)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
