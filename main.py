import cv2
import numpy
from CountsPerSec import CountsPerSec
from VideoGet import VideoGet
from VideoShow import VideoShow
from Process import *

# Initialize cache for contain QRcode query data
cache = Cache()

# Function for prin Iteration rate in frame
def putIterationsPerSec(frame, iterations_per_sec):
    """
    Add iterations per second text to lower-left corner of a frame.
    """
    cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec), (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))
    return frame

# main function
def main(source = 0):
    
    # start cv2.Videocapture's thread
    video_getter = VideoGet(source).start()
    # start cv2.imshow's thread
    video_shower = VideoShow(video_getter.frame).start()
    # start time counter for calculate a iteration rate
    cps = CountsPerSec().start()
    
    # loop for stream frame
    while True:
        
        # check if doesn't has any frame or User press 'Q'
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop() # stop cv2.VideoCapture's thread
            video_getter.stop() # stop cv2.imshow's thread
            break
        
        # init frame as object
        image = Image(video_getter.frame)
        
        # for loop for mactching qrcode and box
        for qr in image.qrlist:
            for box in image.boxlist:
                # check qr is in the box
                if image.QRisinBox(box, qr):
                    
                    # remove box that already used by this qrcode for a next round serching performance
                    image.boxlist.remove(box)
                    # init qrcode to an object and pass parameters with id and cache for append to cache
                    qrcode = Package(qr.get('id'), cache)
                    
                    # qrcode is activated and registeratered
                    if qrcode.IsActivatedIsRegistered:
                        
                        # get the pixel height and width of qrcode and average them
                        dimension = ((qr.get('bottomrightpoint')[0] - qr.get('topleftpoint')[0]) + (qr.get('bottomrightpoint')[1] - qr.get('topleftpoint')[1])) / 2
                        # calculate the ratio for turn a value in pixel unit to centemeter unit. 5 represent to the size of qrcode in centemeter units.
                        ratio = 5 / dimension
                        
                        # get a width and height of the box and round it to decimal point.
                        width, height = (box.get('bottomrightpoint')[0] - box.get('topleftpoint')[0]) * ratio, (box.get('bottomrightpoint')[1] - box.get('topleftpoint')[1]) * ratio
                        width, height, depth, weight = round(width,2), round(height,2), 0, 0

                        # draw the rectangle around the box and qrcode
                        cv2.rectangle(image.frame, box.get('topleftpoint'), box.get('bottomrightpoint'), (0, 200, 200), 2)
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (0, 0, 200), 2)
                        
                        # put text that contain the ID of qrcode and its dimension
                        cv2.putText(image.frame, f"id: {qr.get('id')}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        cv2.putText(image.frame, f"width: {width}, height: {height}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1] + 35), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

                        # write the dimension of the box to the database
                        qrcode.AddDimension(width, height, depth, weight)
                        
                    # qrcode is not activated
                    elif qrcode.NotActivated: 
                        # draw rectangle around qrcode and put status text
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Isn't activated", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
                    # draw rectangle around qrcode and put status text
                    elif qrcode.IsActivatedIsRegistered:
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Isn't Registered", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    # draw rectangle around qrcode and put status text
                    elif qrcode.IsAddDimension:
                        cv2.rectangle(image.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(image.frame, f"Is added dimension", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
                    # break the loop because we found the box that match with this qrcode already.
                    break
        
        # put the iteration rate to frame.
        image.frame = putIterationsPerSec(image.frame, cps.countsPerSec())
        # display frame
        video_shower.frame = image.frame
        # clear cache to 10 items if it has more than 10 items.
        cache.Clear()
        # iteration counter
        cps.increment()


if __name__ == "__main__":
    main()