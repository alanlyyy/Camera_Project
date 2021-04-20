import cv2
import numpy as np

class live_stream:
    """displays live stream from camera."""
    
    def roll(self):
                
        # Create a VideoCapture object
        self.cap = cv2.VideoCapture(0)

        # Check if camera opened successfully
        if (self.cap.isOpened() == False): 
          print("Unable to read camera feed")

        # Default resolutions of the frame are obtained.The default resolutions are system dependent.
        # We convert the resolutions from float to integer.
        self.frame_width = int(self.cap.get(3))
        self.frame_height = int(self.cap.get(4))
        
        while(True):
          ret, frame = self.cap.read()

          if ret == True: 

            # Display the resulting frame    
            cv2.imshow('frame',frame)

            # Press Q on keyboard to stop recording
            if cv2.waitKey(1) & 0xFF == ord('q'):
              break

          # Break the loop
          else:
            break  
        
        # When everything done, release the video capture and video write objects
        self.cap.release()
        
        # Closes all the frames
        cv2.destroyAllWindows()
        
if __name__ == '__main__':
    
    ls = live_stream()
    ls.roll()