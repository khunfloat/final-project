import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path
from threading import Thread

# define the collection of firestore
collection = 'PackageInformation'
# deind servicekey path 
servicekey_path = Path('.', 'ServiceAccountKey.json')
# qrcode size in centimeter units
qrcode_size = 5

# check if the default_app is init already. do not init it.
if not firebase_admin._apps:
    cred = credentials.Certificate(servicekey_path)
    default_app = firebase_admin.initialize_app(cred)

# connect to database
db = firestore.client()

# Package Class for store the information for each package
class Package():
    
    def __init__(self, id, cache):
        
        # init variables
        self.id = id
        self.cache = cache
        
        # Find the qr id in cache. if cache doesn't have it. it will get the data by query the database.
        data = next((item for item in self.cache.cache if item["id"] == self.id), None)
        
        # if cache doesn't have this id
        if data == None:
            self.dict = db.collection(collection).document(self.id).get().to_dict()
            self.activation = self.dict.get('activation')
            self.registeration = self.dict.get('registeration')
            self.dimension_status = False if self.dict.get('dimension_status') == None else True
            
            # append to cache
            self.cache.AddCache({'id' : self.id,
                                 'activation' : self.activation,
                                 'registeration' : self.registeration,
                                 'dimension_status' : self.dimension_status})
            
        # if cache has this id
        else:
            self.activation = data.get('activation')
            self.registeration = data.get('registeration')
            self.dimension_status = False if data.get('dimension_status') == None else True
            
            
        # logic for check package status
        self.IsActivatedIsRegistered = self.activation and self.registeration and (not self.dimension_status)
        self.NotActivated = not self.activation
        self.IsActivatedNotRegistered = self.activation and (not self.registeration)
        self.IsAddDimension = self.dimension_status
        
    # function for add the dimension to database 
    def AddDimension(self, width, height, depth, weight):
        
        db.collection(collection).document(self.id).set({'dimension_status' : True,
                                                        'height' : height, 
                                                        'width' : width,
                                                        'depth' : depth,
                                                        'weight' : weight}, merge=True)

# Cache Class create cache for the package class to get the data if it exists in the cache. for the faster performance
class Cache():
    
    # init variables
    def __init__(self):
        self.cache = []
    
    # add the data to the cache
    def AddCache(self, data):
        self.cache.append(data)
        
    # for clear the list cache when it has more than 10 items. and select a last 10 entries.
    def Clear(self):
        if len(self.cache) > 10:
            self.cache = self.cache[-10:]
        
# Image Class for manage the object in a frame
class Image():
    
    # init variables.
    def __init__(self, frame):
        self.frame = frame
        self.decoded_qr = decode(self.frame, symbols=[ZBarSymbol.QRCODE])
        self.qrlist = self.findqr()
        self.boxlist = self.findbox()
        
    # find qrcode in frame.
    def findqr(self):
        
        qrlist = []
        for qr in self.decoded_qr:
            pts = np.array([qr.polygon], np.int32).reshape((-1, 1, 2))
            qrlist.append({'id' : qr.data.decode('utf-8'),
                            'topleftpoint' : tuple(pts[0][0]),
                            'bottomrightpoint' : tuple(pts[2][0])});
        return qrlist
    
    # find box in frame.
    def findbox(self):
        
        boxlist = []
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_TOZERO)
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            box = np.int0(cv2.boxPoints(rect))
            boxlist.append({'topleftpoint' : tuple(box[0]), 'bottomrightpoint' : tuple(box[2])})     
        return boxlist
    
    # check that qrcode is in the box
    def QRisinBox(self, box, qr):
        
        # check if (min box.x < qr.x < max box.x) and (min box.y < qr.y < max box.y)
        if (box.get('topleftpoint')[0] < qr.get('topleftpoint')[0] < box.get('bottomrightpoint')[0]) and (box.get('topleftpoint')[1] < qr.get('topleftpoint')[1] < box.get('bottomrightpoint')[1]):
            return True
        else:
            return False

class Process():
    
    def __init__(self, frame):
        self.qrlist = []
        self.boxlist = []
        self.frame = frame
        self.decoded_qr = decode(frame)
        
    def findqr(self):

        for qr in self.decoded_qr:
            pts = np.array([qr.polygon], np.int32).reshape((-1, 1, 2))
            self.qrlist.append({'id' : qr.data.decode('utf-8'),
                                'topleftpoint' : tuple(pts[0][0]),
                                'bottomrightpoint' : tuple(pts[2][0])});

    def findbox(self):
        
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_TOZERO)
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            rect = cv2.minAreaRect(cnt)

            box = np.int0(cv2.boxPoints(rect))
            self.boxlist.append({'topleftpoint' : tuple(box[0]), 'bottomrightpoint' : tuple(box[2])})
            
    def matching(self):
        
        self.findqr()
        
        self.findbox()

        for qr in self.qrlist:
            for box in self.boxlist:
                if (box.get('topleftpoint')[0] < qr.get('topleftpoint')[0] < box.get('bottomrightpoint')[0]) and (box.get('topleftpoint')[1] < qr.get('topleftpoint')[1] < box.get('bottomrightpoint')[1]):
                    
                    self.boxlist.remove(box)
                    
                    qrcode = Package(qr.get('id'))
                    
                    if qrcode.IsActivatedIsRegistered:

                        dimension = ((qr.get('bottomrightpoint')[0] - qr.get('topleftpoint')[0]) + (qr.get('bottomrightpoint')[1] - qr.get('topleftpoint')[1])) / 2
                        ratio = 5 / dimension
                        
                        width, height = (box.get('bottomrightpoint')[0] - box.get('topleftpoint')[0]) * ratio, (box.get('bottomrightpoint')[1] - box.get('topleftpoint')[1]) * ratio
                        width, height, depth, weight = round(width,2), round(height,2), 0, 0

                        cv2.rectangle(self.frame, box.get('topleftpoint'), box.get('bottomrightpoint'), (0, 200, 200), 2)
                        cv2.rectangle(self.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (0, 0, 200), 2)
                        
                        cv2.putText(self.frame, f"id: {qr.get('id')}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        cv2.putText(self.frame, f"width: {width}, height: {height}", (box.get('topleftpoint')[0], box.get('topleftpoint')[1] + 35), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

                        qrcode.AddDimension(width, height, depth, weight)

                    elif qrcode.NotActivated: 
                        cv2.rectangle(self.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(self.frame, f"Isn't activated", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    elif qrcode.IsActivatedIsRegistered:
                        cv2.rectangle(self.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(self.frame, f"Isn't Registered", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                    
                    elif qrcode.IsAddDimension:
                        cv2.rectangle(self.frame, qr.get('topleftpoint'), qr.get('bottomrightpoint'), (222, 0, 0), 2)
                        cv2.putText(self.frame, f"Is added dimension", (box.get('topleftpoint')[0], box.get('topleftpoint')[1]), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
                        
                    break
                
    def start(self):
        Thread(target=self.matching, args=()).start()
        return self