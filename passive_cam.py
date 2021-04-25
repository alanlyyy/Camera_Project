#!/usr/bin/env python3

# 2020-09-27
"""
    A Program to read the DHTXX temperature/humidity sensors.

    REQUIREMENTS
    DHT.py    download "module" from http://abyz.me.uk/rpi/pigpio/code/DHT.py
    pigpiod running (sudo pigpiod) before running script
    
    04-10-21
    -Need to set edge trigger interrupt for PIR sensor for recording camera data
    -Need a naming convention for video files
    
    04-11-21
    1. Tested implementing a interupt using pi.callback() function which interfered with timing of DHT11 sensor reading.
    implemented polling and the dht11 sensor is working again.
    
    2. Need to implement file storage process and naming of videos
    
    #04-12-21
    1. Test dht11 polling along with pb polling, there is huge time delay for pressing the pb to invoke the camera, which is not responsive to presses.
    2. Implemented write to subfolders with each subfolder named M-D-Y, each video name contains an epoch time
    3. --Need to implement camera footage overwrite old data feature.
    
    #04-13-21
    1. write test for overwrite old videos
    2. Need to put script into a class, so we can easily import and export functions
"""

#import sys
import pigpio
from dht11_test import DHT_Wrapper
import time
import datetime
import os
from shutil import rmtree

PIR = 27 #actual PIR is 27
DHT_pin = 4
PB = 17

#INPUT PB used to switch between modes and exit program successfully
MODE_SWITCH_PB = 22    #PIN 15,GPIO22
MODE_WRITE_OUTPUT = 23 #PIN 16, GPIO23 

warm_up_time = 60
temp_read_delay_time = 30
camera_record_time = 30
space_limit = 0.70
base_path = '/home/pi/Videos'
camera_record_mode = 1

#https://github.com/opencv/opencv-python/issues/299
fourcc_codec = 'avc1' #for x264 or h264 encoding
cv_write_format = 'mp4'

#if we use mode 1 for passive cam, we are using picamera to save to video.
#otherwise we use  opencv for saving video.
if (camera_record_mode == 1):
    import picamera
else:
    import cv2
    

class Passive_Cam:
    """passive camera mode, records 30s videos when PIR is detected."""
    
    def __init__(self,PI_GPIO,PIR,DHT_pin,CAM_PB,MS_PB,MWO):
        
        self.pi = PI_GPIO
        #store pin numbers
        self.PIR = PIR
        self.DHT_pin = DHT_pin
        self.PB = CAM_PB
        
        #hardware release switch
        self.MS_PB = MS_PB
        self.MWO = MWO
        
        self.pi.set_mode(self.DHT_pin,pigpio.INPUT)   
        self.pi.set_pull_up_down(self.DHT_pin,pigpio.PUD_UP)
        
        #must connect power of PIR with +5V and GND
        self.pi.set_mode(self.PIR, pigpio.INPUT)    #set gpio27 as input
        self.pi.set_pull_up_down(self.PIR,pigpio.PUD_DOWN) #enable pull down resistor
        
        #for push button
        self.pi.set_mode(self.PB, pigpio.INPUT)
        self.pi.set_pull_up_down(self.PB, pigpio.PUD_UP) #enable pull up resistor
        
        self.pi.set_mode(self.MS_PB,pigpio.INPUT)    #set gpio22 as input
        self.pi.set_pull_up_down(self.MS_PB,pigpio.PUD_UP) #enable pull down resistor
        
        self.pi.set_mode(self.MWO,pigpio.OUTPUT)    #set gpio23 as output, for write functionality
        
        self.sensor = DHT_Wrapper(self.pi,self.DHT_pin,1)
        
        print("Warming Up...")
        
        #allow sensor to warm up for 60s before recording
        #camera warm up 
        #DHT11 warm up
        #PIR warm up
        time.sleep(warm_up_time)
        
        print("System is ready...")
        
        self.is_camera_recording = 0
        
        #save the start time
        self.prev_time = time.time()

    def record(self):
    
        self.camera = picamera.PiCamera()
        
        self.is_camera_recording =1
        
        print("Camera is recording..." )
        time.sleep(1)
        
        self.camera.resolution = (640,480)
        
        #create namestring for video
        day = datetime.date.today().strftime("%b-%d-%Y")
        base_fp = "/home/pi/Videos/%s" %day
        fp = "%d.h264" %int(time.time())
        record_fp = os.path.join(base_fp,fp)
        
        #try recording
        try:
            self.camera.start_recording(record_fp)
        
        #if base_fp directory does not exist
        #generate directory, continue to record video.
        except:
            os.mkdir(base_fp)
            self.camera.start_recording(record_fp)
            
        
        #record video for 30s
        self.camera.wait_recording(camera_record_time)
        self.camera.stop_recording()
        
        self.is_camera_recording = 0
        print("Camera Stop recording...")
        
        self.camera.close()
    
    def record_cv2(self):
        """
        Test recording module. Not working correctly
        https://github.com/opencv/opencv-python/issues/299
        
        avc1 codec is for h264 encoding, use with mp4 or avi file format.
        
        Not able to record more than 2second video.
        Camera shuts off by itself.
        """
        print("Camera Start Recording...")
        cap = cv2.VideoCapture(0)
        
        #create namestring for video
        day = datetime.date.today().strftime("%b-%d-%Y")
        base_fp = "/home/pi/Videos/%s" %day
        fp = "%d.%s" % (int(time.time()), cv_write_format)
        record_fp = os.path.join(base_fp,fp)
        prev_time = time.time()
        
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(fourcc_codec)
        out = cv2.VideoWriter(record_fp,fourcc, 30.0, (640,480))
        
        #record for 15 seconds
        while((time.time() - prev_time) < camera_record_time):
            
            ret, frame = cap.read()
            
            if ret==True:
                out.write(frame)
            
            else:
                break
        
        # Release everything if job is finished
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        print("Camera Stop Recording...")

    
    def disk_usage(self,path):
        """return diskspace usage.
        manpages: https://linux.die.net/man/2/statvfs
        solution: https://stackoverflow.com/questions/54458308/how-to-get-disk-space-total-used-and-free-using-python-2-7-without-psutil
        """
        
        #object that holds disk usage information in bytes
        st = os.statvfs(path)
        
        #f_bavail free blocks for unprivileged users
        #f_frsize fragment size 
        free = st.f_bavail * st.f_frsize
        
        #f_blocks size of free space in f_frsize units
        total = st.f_blocks * st.f_frsize
        
        #f_blocks total available 
        used = (st.f_blocks  - st.f_bfree) * st.f_frsize
        return (total, free, used)

    def delete_old_video(self,path):
        """
        if disk usage is met, delete oldest video directory.
        """
        
        list_of_dir = os.listdir(path)
        
        #print(list_of_dir)
        
        if (len(list_of_dir) == 0):
            return
            
        oldest_directory = os.path.join(path,list_of_dir[0])
        
        for file in range (1, len(list_of_dir)):
            
            #get current directory
            current_directory = os.path.join(path, list_of_dir[file])
            
            #if oldest directory < current directory, replace oldest directory
            if ( os.path.getmtime(current_directory) < os.path.getmtime(oldest_directory) ):
                
                oldest_directory = current_directory 
                #print(oldest_directory)
                
        #remove directory and all files in the directory.
        rmtree(oldest_directory)
    
    def roll(self):
        
        #if we detect a high signal at GPIO27 start recording.
        #by default pin GPIO27 is pulled down to ground.
        if (self.pi.read(self.PIR) == 1):
        
            #pir has already been activated.
            self.PIR_FLAG = 1
            
            #if camera is already recording break out of loop
            if (self.is_camera_recording == 0):
                
                if (camera_record_mode == 1):
                    self.record()
                    time.sleep(1)
                else:
                    self.record_cv2()
                    time.sleep(1)
        
        curr_time = time.time()
        
        #get temperature reading every minute
        if ((curr_time - self.prev_time) > temp_read_delay_time):
            
            self.sensor.get_current_temperature_reading()
            print("Getting Current Temperature reading.")
            print("Current Temp: ", self.sensor.get_last_temp_reading())
            
            #if temperature measured is greater than or equal to 50C
            if (self.sensor.get_last_temp_reading() >= 50):
                
                print("Temperature is over 50C...")
                
                #turn on the fan for 30s
                print("turn on the fan for 30s")
                while ((time.time() - curr_time) < 30):
                    pass
            
            #update the new prev time with curr_time
            self.prev_time = curr_time
        
        #get current disk usage
        total, free, used = self.disk_usage(base_path)
        
        #delete old video if disk usage is met.
        if ((used/total) >= space_limit):
            self.delete_old_video(base_path)
        
        #place holder for gui button, if live stream button is pressed release camera resources and exit
        if (self.pi.read(self.MS_PB)==0):
            return 0
                
if __name__ == '__main__':

    #setup DHT11 sensor
    #run pigpiod before executing rest of the script.
    try:
        os.system("sudo pigpiod")
    except:
        print("daemon already running")

    #global variable to control gpio
    pi = pigpio.pi()
    if not pi.connected:
        exit()
    
    cam = Passive_Cam(pi,PIR,DHT_pin,PB,MODE_SWITCH_PB,MODE_WRITE_OUTPUT)
    
    while True:
        if (cam.roll() == 0):
            break
    
    #stop pi.gpio connection
    pi.stop()
    
        
        
        