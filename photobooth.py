#!/usr/bin/env python

from Tkinter import *
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64,tkFont,time,smtplib
import sys
import traceback
from ptp.PtpUsbTransport import PtpUsbTransport
from ptp.PtpSession import PtpSession, PtpException
from ptp import PtpValues
from PIL import Image
import re

qtext = '[^\\x0d\\x22\\x5c\\x80-\\xff]'
dtext = '[^\\x0d\\x5b-\\x5d\\x80-\\xff]'
atom = '[^\\x00-\\x20\\x22\\x28\\x29\\x2c\\x2e\\x3a-\\x3c\\x3e\\x40\\x5b-\\x5d\\x7f-\\xff]+'
quoted_pair = '\\x5c[\\x00-\\x7f]'
domain_literal = "\\x5b(?:%s|%s)*\\x5d" % (dtext, quoted_pair)
quoted_string = "\\x22(?:%s|%s)*\\x22" % (qtext, quoted_pair)
domain_ref = atom
sub_domain = "(?:%s|%s)" % (domain_ref, domain_literal)
word = "(?:%s|%s)" % (atom, quoted_string)
domain = "%s(?:\\x2e%s)*" % (sub_domain, sub_domain)
local_part = "%s(?:\\x2e%s)*" % (word, word)
addr_spec = "%s\\x40%s" % (local_part, domain)

sys.path.append("../")
from smtp_creds import *


email_validate = re.compile('\A%s\Z' % addr_spec)


root = Tk()
root.title("Burton 1 Photobooth!")
#root.overrideredirect(1)
root.geometry("1024x640")
root.focus_set() # <-- move focus to this widget
#root.bind("<Escape>", lambda e: e.widget.quit())
root.bind("|", lambda e: e.widget.quit())

image_file = 'b1logo.png'


class App:
	def __init__(self, master):
		
		self.master = master
		frame = Frame(master, bg="white", height=680, pady=65)
		frame.pack()
		frame.focus_set()

		self.status=StringVar()
		self.status.set("")

		self.main_font = tkFont.Font(family="Helvetica", size=36)
		self.small_font = tkFont.Font(family="Helvetica", size=24)
		self.go_text = Label(frame, font=self.small_font, textvariable=self.status,bg="white")
		self.go_text.pack(side=BOTTOM)

		self.b1_logo = PhotoImage(file='b1logo.gif')
		self.stage = Label(frame,textvariable=self.status, image=self.b1_logo,bg="white")
		self.stage.pack(side=LEFT)

		self.input_form = Frame(frame, padx=40,bg="white")
		self.input_form.pack(side=RIGHT)

		self.welcome_text = Label(self.input_form, anchor=W,bg="white", width=300, justify=LEFT, font=self.main_font, text="Please type in your names, ")
		self.welcome_text_small = Label(self.input_form, anchor=W,bg="white", width=300, justify=LEFT, text="separated by commas, so we can tag you on Facebook and G+!")
		self.welcome_text.pack(side=TOP, expand=1)
		self.welcome_text_small.pack(side=TOP, expand=1)

		self.names_entry = Entry(self.input_form, width=100, font=self.small_font)
		self.names_entry.pack(side=TOP)
		self.spacer = Frame(self.input_form, width=500, height=40,bg="white")
		self.spacer.pack(side=TOP)


                self.welcome_text2 = Label(self.input_form, anchor=W,bg="white", width=300, justify=LEFT, font=self.main_font, text="and your emails,")
                self.welcome_text_small2 = Label(self.input_form,bg="white", anchor=W, width=300, justify=LEFT, text="so we can send you the photos!")
                self.welcome_text2.pack(side=TOP, expand=1)
                self.welcome_text_small2.pack(side=TOP, expand=1)

		self.email_entry = Entry(self.input_form, width=100, font=self.small_font)
		self.email_entry.pack(side=TOP)

                self.spacer = Frame(self.input_form, width=500, height=40,bg="white")
                self.spacer.pack(side=TOP)

		self.go = Button(self.input_form, font=self.main_font, text="Go!", fg="red", command=self.take_photo)
		self.go.pack(side=TOP)
		self.names_entry.focus()

		self.send_ip()

	def take_photo(self):
		print "Click!"
		self.mesg = []
		self.mesg.append("5...")
		self.mesg.append("5...4...")
		self.mesg.append("5...4...3...")
		self.mesg.append("5...4...3...2...")
		self.mesg.append("5...4...3...2...1... SMILE!!!")
		self.mesg.append("Smile!")
		self.mesg.append("Smile Again!")
		self.mesg.append("Smile Again Again!")
		self.mesg.append("Smile for the last time!")
		self.mesg.append("Thank You! Please wait while I think...")
		self.status.set("Get ready! I'm going to count down and take 4 photos!")
		self.go.config(state=DISABLED)
		self.names_entry.config(state=DISABLED)
		self.email_entry.config(state=DISABLED)
		self.master.after(2000, self.take_photo_next_stage, 0)
	
	def take_photo_next_stage(self, state):
		self.master.bell()
		
		# a weird hack
		if (state < 5 or state==9):
			self.status.set(self.mesg[state])
		else:	
			self.status.set(self.mesg[state+1])

		if (state == 5):	
			self.open_camera()
		if (state>=5 and state<9):
			#print "Took photo"
			self.capture_image()
			self.master.after(500, self.take_photo_next_stage,state+1)
		if (state==9):
			self.finish_capture()
			self.combine_photos()
			self.send_photos()
			self.email_entry.delete(0, END)
			self.names_entry.delete(0, END)
			#assemble
			#send email
		if (state<5):
			self.master.after(1000, self.take_photo_next_stage,state+1)


			
	def send_photos(self):
			COMMASPACE = ', '
			# Create the container (outer) email message.
			msg = MIMEMultipart()
			msg['Subject'] = self.names_entry.get().replace(","," &")+' at the Burton One Photobooth'
			# me == the sender's email address
			# family = the list of all recipients' email addresses
			msg['From'] = "b1-photobooth@mit.edu"
			msg['To'] = self.email_entry.get()
			msg['Bcc'] = "eadams@mit.edu"
			msg.preamble = 'Burton One Photobooth!'
			
			# Assume we know that the image files are all in PNG format
			fp = open("b1photo.jpg", 'rb')
			img = MIMEImage(fp.read())
			fp.close()
			msg.attach(img)
			
			# Send the email via our own SMTP server.
			s = smtplib.SMTP('outgoing.mit.edu', 587)
			s.starttls()
			s.login(USER,PW)
			#print self.email_entry.get()
			toaddrs = self.email_entry.get().replace(",", "").split()
			toaddrs.append("eadams@mit.edu")
			to_final = []
			for e in toaddrs:
				if email_validate.match(e):
					to_final.append(e)
			s.sendmail("b1-photobooth@mit.edu", to_final, msg.as_string())
			s.quit()
			self.status.set("Photos sent!!")
			self.go.config(state=NORMAL)
			self.names_entry.config(state=NORMAL)
			self.email_entry.config(state=NORMAL)
			self.names_entry.focus()
			self.master.after(1000, self.reset_status)

        def send_ip(self):
                        COMMASPACE = ', '
			import subprocess
			ip = "Hello! I'm alive!!!!! Here's my IP info:\n\n%s\n\n \tLove, B1 Photobooth" % subprocess.Popen(['/sbin/ifconfig'], stdout=subprocess.PIPE).communicate()[0]
                        # Create the container (outer) email message.
                        msg = MIMEMultipart()
                        msg['Subject'] = 'B1 Photobooth just booted up!'
                        # me == the sender's email address
                        # family = the list of all recipients' email addresses
                        msg['From'] = "b1-photobooth@mit.edu"
                        msg['To'] = self.email_entry.get()
                        msg['Bcc'] = "eadams@mit.edu"
                        msg.preamble = 'Burton One Photobooth IP Info!'

                        # Assume we know that the image files are all in PNG format
                        fp = open("b1photo.jpg", 'rb')
                        img = MIMEImage(fp.read())
                        fp.close()
			txt = MIMEText(ip)
			msg.attach(txt)
                        msg.attach(img)

                        # Send the email via our own SMTP server.
                        s = smtplib.SMTP('outgoing.mit.edu', 587)
                        s.starttls()
                        s.login('eadams','b1ph0t0b00th')
                        #print self.email_entry.get()
                        toaddrs = ["eadams@mit.edu", "burton1-officers@mit.edu", "benb@mit.edu"]
                        to_final = []
                        for e in toaddrs:
                                if email_validate.match(e):
                                        to_final.append(e)
                        s.sendmail("b1-photobooth@mit.edu", to_final, msg.as_string())
                        s.quit()
                        self.status.set("Photos sent!!")
                        self.go.config(state=NORMAL)
                        self.names_entry.config(state=NORMAL)
                        self.email_entry.config(state=NORMAL)
                        self.names_entry.focus()
                        self.master.after(1000, self.reset_status)
			
	def reset_status(self):
		self.status.set("")
					
	def open_camera(self):
		self.ptpTransport = PtpUsbTransport(PtpUsbTransport.findptps()[0])
		self.ptpSession = PtpSession(self.ptpTransport)		
		self.vendorId = PtpValues.Vendors.STANDARD
		try:
			self.ptpSession.OpenSession()
			self.deviceInfo = self.ptpSession.GetDeviceInfo()
			self.vendorId = self.deviceInfo.VendorExtensionID
		except PtpException, e:
			print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, self.vendorId)
		except Exception, e:
			print "An exception occurred: %s" % e
			traceback.print_exc()
			
		self.images = []
	
	def capture_image(self):
		try:
			self.ptpSession.InitiateCapture(objectFormatId=PtpValues.StandardObjectFormats.EXIF_JPEG)
			objectid = None
			while True:
				evt = self.ptpSession.CheckForEvent(None)
				if evt == None:
					raise Exception("Capture did not complete")
				if evt.eventcode == PtpValues.StandardEvents.OBJECT_ADDED:
					objectid = evt.params[0]
					self.images.append(objectid)
					break
		except PtpException, e:
			print "PTP Exception: %s" % PtpValues.ResponseNameById(e.responsecode, self.vendorId)
		except Exception, e:
			print "An exception occurred: %s" % e
			traceback.print_exc()

	def finish_capture(self):
		self.status.set("Photos transfered!")
		id = 0
		if len(self.images) > 0:
			for objectid in self.images:
				file = open("capture_%i.jpg" % id, "w")
				self.ptpSession.GetObject(objectid, file)
				file.close()
				id+=1
				self.ptpSession.DeleteObject(objectid)
		del self.ptpSession
		del self.ptpTransport
	
	def combine_photos(self):
		comp = Image.new('RGBA', (484,1296+190), (255, 255, 255, 255))
		for i in range(4):
			img=Image.open('capture_'+str(i)+'.jpg','r')
			img.thumbnail((484,324), Image.ANTIALIAS)
			comp.paste(img, (0, i*324))
		img=Image.open('B1_watermark.png','r')
		comp.paste(img, (0, 4*324))
		comp.save("b1photo.jpg")
		self.status.set("Made a comp!")
		
app = App(root)
root.mainloop() 
