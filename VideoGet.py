from threading import Thread
import cv2
from DepthCamera import DepthCamera

class VideoGet:

    def __init__(self, src=0):
        self.stream = DepthCamera()
        (self.grabbed, self.depth_frame, self.color_frame) = self.stream.get_frame()
        self.stopped = False

    def start(self): 
        # start cv2.Videocapture's thread  
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.depth_frame, self.color_frame) = self.stream.get_frame()

    def stop(self):
        self.stopped = True