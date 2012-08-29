#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import traceback
import time
import ptp.PtpAbstractTransport
import ptp.NikonSupport
from ptp.PtpUsbTransport import PtpUsbTransport
from ptp.PtpSession import PtpSession, PtpException
from ptp import PtpValues

ptpTransport = PtpUsbTransport(PtpUsbTransport.findptps()[0])
ptpSession = PtpSession(ptpTransport)

# seen d109, d10b, d16a
rw_vals = (0xd01f, 0xd045, 0xd109, 0xd10b, 0xd16a)
ro_vals = (0xd0c3, 0xd0e1, 0xd0e2, 0xd102, 0xd120, 0xd121, 0xd122, 0xd124, 0xd125)

vendorId = PtpValues.Vendors.STANDARD
try:
    ptpSession.OpenSession()
    deviceInfo = ptpSession.GetDeviceInfo()
    vendorId = deviceInfo.VendorExtensionID

#    print "%i" % ptpSession.GetDevicePropValue(0xd126, False, "b")
    
    for id in rw_vals:
        print "RW: %04x: %02x" % (id, ptpSession.GetDevicePropValue(id, False, "B"))
    print
    for id in ro_vals:
        print "RO: %04x: %02x" % (id, ptpSession.GetDevicePropValue(id, False, "B"))


except PtpException, e:
    print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, vendorId)
except Exception, e:
    print "An exception occurred: %s" % e
    traceback.print_exc()

del ptpSession
del ptpTransport
