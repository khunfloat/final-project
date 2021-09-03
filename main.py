import cv2
import numpy
from CountsPerSec import CountsPerSec
from VideoGet import VideoGet
from VideoShow import VideoShow
from Process import Package, Image, Cache

# Initialize cache for contain QRcode query data
cache = Cache()

# Function for prin Iteration rate in frame
def putIterationsPerSec(frame, iterations_per_sec):
    """
    Add iterations per second text to lower-left corner of a frame.
    """
    cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec), (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))
    return frame

# check that qrcode is in the box
def QRisinBox(box, qr):
    
    # check if (min box.x < qr.x < max box.x) and (min box.y < qr.y < max box.y)
    qrpt, boxpt = [item[0] for item in qr.get('pts')], box.get('pts')

    qrzip, boxzip = tuple(zip(qrpt[0], qrpt[1], qrpt[2], qrpt[3])), tuple(zip(boxpt[0], boxpt[1], boxpt[2], boxpt[3]))

    # x
    minx, maxx = min(boxzip[0]), max(boxzip[0])

    # y
    miny, maxy = min(boxzip[1]), max(boxzip[1])

    if all(x in range(minx, maxx) for x in qrzip[0]) and all(y in range(miny, maxy) for y in qrzip[1]):
        return True

    else:
        return False
    

# value from this func is in centimeter unit
def get_depth(x:int, y:int) -> float:
    '''value from this func is in centimeter unit'''
    return (depth_frame[(int(y), int(x))]) / 10

# main function
def main(source = 0):
    
    # start cv2.Videocapture's thread
    video_getter = VideoGet(source).start()
    # start cv2.imshow's thread
    video_shower = VideoShow(video_getter.color_frame).start()
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
        image = Image(video_getter.color_frame)

        # for loop for mactching qrcode and box
        for qr in image.qrlist:
            for box in image.boxlist:
                # check qr is in the box
                if QRisinBox(box, qr):
                    
                    # remove box that already used by this qrcode for a next round serching performance
                    # image.boxlist.remove(box)
                    
                    # init qrcode to an object and pass parameters with id and cache for append to cache
                    package = Package(qr, box, cache)
                    
                    # qrcode is activated and registeratered
                    if package.IsActivatedIsRegistered:
                        
                        # get the pixel height and width of qrcode and average them
                        dimension = (package.QRheight + package.QRwidth) / 2
                        # calculate the ratio for turn a value in pixel unit to centemeter unit. 5 represent to the size of qrcode in centemeter units.
                        ratio = 5 / dimension
                        
                        # get a width and height of the box and round it to decimal point.
                        width, height = package.BOXwidth * ratio, package.BOXheight * ratio
                        width, height, depth, weight = round(width,2), round(height,2), 0, 0

                        # draw the rectangle around the box and qrcode
                        cv2.polylines(image.frame, [package.QRpts], True, (255, 0 ,0), 3)
                        cv2.polylines(image.frame, [package.BOXpts], True, (0, 111 ,111), 3)    
                        
                        # put text that contain the ID of qrcode and its dimension
                        cv2.putText(image.frame, f"id: {qr.get('id')}", package.BOXpts[0][0], cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        cv2.putText(image.frame, f"width: {width}, height: {height}", (package.BOXpts[0][0], package.BOXpts[0][1] + 35), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

                        # write the dimension of the box to the database
                        package.AddDimension(width, height, depth, weight)
                        
                    # qrcode is not activated
                    elif package.NotActivated: 
                        # draw rectangle around qrcode and put status text
                        cv2.polylines(image.frame, [package.QRpts], True, (255, 0 ,0), 3)
                        cv2.polylines(image.frame, [package.BOXpts], True, (0, 111 ,111), 3) 
                        cv2.putText(image.frame, f"Isn't activated", package.BOXpts[0], cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
                    # draw rectangle around qrcode and put status text
                    elif package.IsActivatedIsRegistered:
                        cv2.polylines(image.frame, [package.QRpts], True, (255, 0 ,0), 3)
                        cv2.polylines(image.frame, [package.BOXpts], True, (0, 111 ,111), 3) 
                        cv2.putText(image.frame, f"Isn't Registered", package.BOXpts[0], cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    # draw rectangle around qrcode and put status text
                    elif package.IsAddDimension:
                        cv2.polylines(image.frame, [package.QRpts], True, (255, 0 ,0), 3)
                        cv2.polylines(image.frame, [package.BOXpts], True, (0, 111 ,111), 3) 
                        cv2.putText(image.frame, f"Is added dimension", package.BOXpts[0], cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
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