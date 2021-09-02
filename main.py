import cv2
import numpy as np
from CountsPerSec import CountsPerSec
from VideoGet import VideoGet
import warnings
from VideoShow import VideoShow
from Process import *

cache = Cache()
warnings.filterwarnings("ignore")

def putIterationsPerSec(frame, iterations_per_sec):
    """
    Add iterations per second text to lower-left corner of a frame.
    """
    cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec),
        (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))
    return frame

def main():
    
    source = 0

    video_getter = VideoGet(source).start()
    video_shower = VideoShow(video_getter.frame).start()
    cps = CountsPerSec().start()
    
    while True:
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop()
            video_getter.stop()
            break
        
        image = Image(video_getter.frame)

        for qr in image.qrlist:
            for box in image.boxlist:
                if image.QRisinBox(box, qr):
                    
                    image.boxlist.remove(box)
                    qrcode = Package(qr.get('id'), cache)
                    
                    if qrcode.IsActivatedIsRegistered:

                        dimension = ((qr.get('bottomrightpoint')[0] - qr.get('topleftpoint')[0]) + (qr.get('bottomrightpoint')[1] - qr.get('topleftpoint')[1])) / 2
                        ratio = 5 / dimension
                        
                        width, height = (box.get('bottomrightpoint')[0] - box.get('topleftpoint')[0]) * ratio, (box.get('bottomrightpoint')[1] - box.get('topleftpoint')[1]) * ratio
                        width, height, depth, weight = round(width,2), round(height,2), 0, 0

                        cv2.rectangle(image.frame, box.get('topleftpoint'), box.get('bottomrightpoint'), (0, 200, 200), 2)
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (0, 0, 200), 2)
                        
                        cv2.putText(image.frame, f"id: {qr.get('id')}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        cv2.putText(image.frame, f"width: {width}, height: {height}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1] + 35), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

                        qrcode.AddDimension(width, height, depth, weight)

                    elif qrcode.NotActivated: 
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Isn't activated", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    elif qrcode.IsActivatedIsRegistered:
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Isn't Registered", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
                    elif qrcode.IsAddDimension:
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Is added dimension", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    break
        
        image.frame = putIterationsPerSec(image.frame, cps.countsPerSec())
        video_shower.frame = image.frame
        cache.Clear()
        cps.increment()


if __name__ == "__main__":
    main()