 # All packages needed for the program are imported ahead
import cv2
import numpy as np
import pyautogui

# Some global variables or others that need prior intialization are initalized here

# colour ranges for feeding to the inRange funtions 
blue_range = np.array([[88,78,20],[128,255,255]])
green_range = np.array([[45,100,50],[75,255,255]])
red_range = np.array([[158,85,72],[180 ,255,255]])

# Prior initialization of all centers for safety
b_cen, g_pos, r_cen = [240,320],[240,320],[240,320]
cursor = [960,540]

# Area ranges for contours of different colours to be detected
r_area = [100,1700]
b_area = [100,1700]
g_area = [100,1700]

# Rectangular kernal for eroding and dilating the mask for primary noise removal 
kernel = np.ones((7,7),np.uint8)

# Status variables defined globally
perform = False
showCentroid = False

# 'nothing' function is useful when creating trackbars
# It is passed as last arguement in the cv2.createTrackbar() function
def nothing(x):
    pass

# To bring to the top the contours with largest area in the specified range
# Used in drawContour()
def swap( array, i, j):
    temp = array[i]
    array[i] = array[j]
    array[j] = temp

# Distance between two centroids
def distance( c1, c2):
        distance = pow( pow(c1[0]-c2[0],2) + pow(c1[1]-c2[1],2) , 0.5)
        return distance

# To toggle status of control variables
def changeStatus(key):
        global perform
        global showCentroid
        global green_range,red_range,blue_range
        # toggle mouse simulation
        if key == ord('p'):
                perform = not perform
                if perform:
                        print ('Mouse ON...')
                else:
                        print ('Mouse OFF...')
        
        # toggle display of centroids
        elif key == ord('c'):
                showCentroid = not showCentroid
                if showCentroid:
                        print ('Show Centroids...')
                else:
                        print ('Remove Centroids...')

        elif key == ord('r'):
                print ('**********************************************************************')
                print ('        			Recalibration mode.')
                print (' Use the trackbars to calibrate and press SPACE when done.')
                print ('        Press D to use the default settings')
                print ('**********************************************************************')

                green_range = calibrateColor('Green', green_range)
                red_range = calibrateColor('Red', red_range)
                blue_range = calibrateColor('Blue', blue_range)                 
        
        else:
                pass

# cv2.inRange function is used to filter out a particular color from the frame
# The result then undergoes morphosis i.e. erosion and dilation
# Resultant frame is returned as mask 
def makeMask(hsv_frame, color_Range):
        
        mask = cv2.inRange( hsv_frame, color_Range[0], color_Range[1])
        # Morphosis is next ...
        eroded_value = cv2.erode( mask, kernel, iterations=1)
        dilated_value = cv2.dilate( eroded_value, kernel, iterations=1)
        
        return dilated_value

# Contours on the mask are detected.. Only those lying in the previously set area 
# range are filtered out and the centroid of the largest of these is drawn and returned 
def drawCentroid(vid, color_area, mask, showCentroid):
        
        contour, _ = cv2.findContours( mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        l=len(contour)
        area = np.zeros(l)

        # filtering contours on the basis of area range specified globally 
        for i in range(l):
                if cv2.contourArea(contour[i])>color_area[0] and cv2.contourArea(contour[i])<color_area[1]:
                        area[i] = cv2.contourArea(contour[i])
                else:
                        area[i] = 0
        
        a = sorted( area, reverse=True) 

        # bringing contours with largest valid area to the top
        for i in range(l):
                for j in range(1):
                        if area[i] == a[j]:
                                swap( contour, i, j)

        if l > 0 :              
                # finding centroid using method of 'moments'
                M = cv2.moments(contour[0])
                if M['m00'] != 0:
                        cx = int(M['m10']/M['m00'])
                        cy = int(M['m01']/M['m00'])
                        center = (cx,cy)
                        if showCentroid:
								#image = cv2.circle(image, center_coordinates, radius, color, thickness) 
                                cv2.circle( vid, center, 5, (0,0,255), -1)
                                        
                        return center
        else:
                # return error handling values
                return (-1,-1)

# This function helps in filtering the required colored objects from the background
def calibrateColor(color, def_range):
        
        global kernel
        name = 'Calibrate '+ color
        cv2.namedWindow(name)
		# colors (hue or tint) in terms of their shade (saturation or amount of gray) and their brightness value.
        cv2.createTrackbar('Hue', name, def_range[0][0]+20, 180, nothing)
        cv2.createTrackbar('Sat', name, def_range[0][1]   , 255, nothing)
        cv2.createTrackbar('Val', name, def_range[0][2]   , 255, nothing)
        while(1):
                ret , frameinv = cap.read()
                frame=cv2.flip(frameinv ,1)

                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                hue = cv2.getTrackbarPos('Hue', name)
                sat = cv2.getTrackbarPos('Sat', name)
                val = cv2.getTrackbarPos('Val', name)

                lower = np.array([hue-20,sat,val])
                upper = np.array([hue+20,255,255])

                mask = cv2.inRange(hsv, lower, upper)
                eroded = cv2.erode( mask, kernel, iterations=1)
                dilated = cv2.dilate( eroded, kernel, iterations=1)

                cv2.imshow(name, dilated)               

                k = cv2.waitKey(5) & 0xFF
                if k == ord(' '):
                        cv2.destroyWindow(name)
                        return np.array([[hue-20,sat,val],[hue+20,255,255]])
                elif k == ord('d'):
                        cv2.destroyWindow(name)
                        return def_range

'''
This function takes as input the center of green region (gc) and 
the previous cursor position (pyp). The new cursor position is calculated 
in such a way that the mean deviation for desired steady state is reduced.
'''
def setCursorPos( gc, pyp):
        
        gp = np.zeros(2)
        
        if abs(gc[0]-pyp[0])<5 and abs(gc[1]-pyp[1])<5:
                gp[0] = gc[0] + .7*(pyp[0]-gc[0]) 
                gp[1] = gc[1] + .7*(pyp[1]-gc[1])
        else:
                gp[0] = gc[0] + .1*(pyp[0]-gc[0])
                gp[1] = gc[1] + .1*(pyp[1]-gc[1])
        
        return gp

# Depending upon the relative positions of the three centroids, this function chooses whether 
# the user desires free movement of cursor, left click, right click or dragging
def chooseAction(gp, rc, bc):
        out = np.array(['move', 'false'])
        if rc[0]!=-1 and bc[0]!=-1:
                
                if distance(gp,rc)<50 and distance(gp,bc)<50 and distance(rc,bc)<50 :
                        out[0] = 'drag'
                        out[1] = 'true'
                        return out
                elif distance(gp,bc)<50: 
                        out[0] = 'right'
                        return out
                elif distance(gp,rc)<50:        
                        out[0] = 'left'
                        return out
                elif distance(gp,rc)<90 and distance(rc,bc)>150:
                        out[0] = 'down'
                        return out      
                elif distance(gp,rc)>90 and distance(rc,bc)>150:
                        out[0] = 'up'
                        return out
                else:
                        return out

        else:
                out[0] = -1
                return out              

# Movement of cursor on screen, left click, right click,scroll up, scroll down
# and dragging actions are performed here based on value stored in 'action'.  
def performAction( gp, rc, bc, action, drag, perform):
        if perform:
                cursor[0] = 4*(gp[0]-110)
                cursor[1] = 4*(gp[1]-120)
                if action == 'move':
                        if gp[0]>110 and gp[0]<590 and gp[1]>120 and gp[1]<390:
                                pyautogui.moveTo(cursor[0],cursor[1])
                        elif gp[0]<110 and gp[1]>120 and gp[1]<390:
                                pyautogui.moveTo( 8 , cursor[1])
                        elif gp[0]>590 and gp[1]>120 and gp[1]<390:
                                pyautogui.moveTo(1912, cursor[1])
                        elif gp[0]>110 and gp[0]<590 and gp[1]<120:
                                pyautogui.moveTo(cursor[0] , 8)
                        elif gp[0]>110 and gp[0]<590 and gp[1]>390:
                                pyautogui.moveTo(cursor[0] , 1072)
                        elif gp[0]<110 and gp[1]<120:
                                pyautogui.moveTo(8, 8)
                        elif gp[0]<110 and gp[1]>390:
                                pyautogui.moveTo(8, 1072)
                        elif gp[0]>590 and gp[1]>390:
                                pyautogui.moveTo(1912, 1072)
                        else:
                                pyautogui.moveTo(1912, 8)
                                
                elif action == 'left':
                        pyautogui.click(button = 'left')

                elif action == 'right':
                        pyautogui.click(button = 'right')
                        
                elif action == 'up':
                        pyautogui.scroll(5)
                        
                elif action == 'down':
                        pyautogui.scroll(-5)
                                                
                elif action == 'drag' and drag == 'true':
                        global g_pos
                        drag = 'false'
                        pyautogui.mouseDown()
                        
                        while(1):
                            k = cv2.waitKey(10) & 0xFF
                            changeStatus(k)
                            _, frameinv = cap.read()
                            # flip horizontaly to get mirror image in camera
                            frame = cv2.flip( frameinv, 1)

                            hsv = cv2.cvtColor( frame, cv2.COLOR_BGR2HSV)
                            b_mask = makeMask( hsv, blue_range)
                            r_mask = makeMask( hsv, red_range)
                            g_mask = makeMask( hsv, green_range)
                            
                            pg_pos = g_pos
                            b_cen = drawCentroid( frame, b_area, b_mask, showCentroid)
                            r_cen = drawCentroid( frame, r_area, r_mask, showCentroid)
                            g_cen = drawCentroid( frame, g_area, g_mask, showCentroid)

                            if      pg_pos[0]!=-1 and g_cen[0]!=-1:
                                g_pos = setCursorPos(g_cen, pg_pos)

                            performAction(g_pos,r_cen, b_cen, 'move', drag, perform)
                            cv2.imshow('FINGER GESTURE', frame)

                            if distance(g_pos,r_cen)>50 or distance(g_pos,b_cen)>50 or distance(r_cen,b_cen)>50:
                                break
                        
                        pyautogui.mouseUp()
                                
                

cap = cv2.VideoCapture(0)

print ('----------------------------------------------------------------------')
print ('                    CALIBRATION MODE')
print (' Use the trackbars to calibrate and press SPACE when done.')
print ('        Press D to use the default settings.')
print ('**********************************************************************')

green_range = calibrateColor('Green', green_range)
red_range = calibrateColor('Red', red_range)
blue_range = calibrateColor('Blue', blue_range)
print ('        Calibration Successfull...')

#cv2.namedWindow('Frame')

print ('**********************************************************************')
print ('        Press P to turn ON and OFF mouse simulation.')
print ('        Press C to display the centroid of various colours.')
print ('        Press R to recalibrate color ranges.')
print ('        Press ESC to exit.')
print ('**********************************************************************')

while(1):

        k = cv2.waitKey(10) & 0xFF
        changeStatus(k)


        _, frameinv = cap.read()
        # flip horizontaly to get mirror image in camera
        frame = cv2.flip( frameinv, 1)

        hsv = cv2.cvtColor( frame, cv2.COLOR_BGR2HSV)

        b_mask = makeMask( hsv, blue_range)
        r_mask = makeMask( hsv, red_range)
        g_mask = makeMask( hsv, green_range)

        pg_pos = g_pos 

        b_cen = drawCentroid( frame, b_area, b_mask, showCentroid)
        r_cen = drawCentroid( frame, r_area, r_mask, showCentroid)      
        g_cen = drawCentroid( frame, g_area, g_mask, showCentroid)
        
        if      pg_pos[0]!=-1 and g_cen[0]!=-1 and g_pos[0]!=-1:
                g_pos = setCursorPos(g_cen, pg_pos)

        output = chooseAction(g_pos, r_cen, b_cen)                      
        if output[0]!=-1:
                performAction(g_pos, r_cen, b_cen, output[0], output[1], perform)       
        
        cv2.imshow('FINGER GESTURE', frame)

        if k == 27:
                break
cap.release()
cv2.destroyAllWindows()