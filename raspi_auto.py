# Python script to handle server side. To be started manually.
# Receives controlling data from UI, processess it and sends it into Arduino via USB (serial).
# Sends low quality video and higher quality pictures to UI.

import asyncio              # For managing multiple asyncronous operations at the same time
import websockets           # For connection between server and UI
import json                 # For packaking data into practical form for transfer between server and UI 
import serial               # For communication between Raspberry Pi and Arduino using USB-cable
import websockets.server    # For connection between server and UI
import datetime             # For getting correct date and time for picture folders
import RPi.GPIO as GPIO     # For servos
import cv2                  # For camera usage and manipulating pictures
import base64               # For encoding images and video frames into base64 format, so they can be safely transmitted over WebSockets as ASCII data
import os                   # For creating directories for pictures


# Open serial connection to Arduino. Name may vary and that is why trying two different names
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
except:
    ser = serial.Serial('/dev/ttyACM1', 9600, timeout=1)

# Set GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Configure servo for vertical camera movement
SERVO_PIN_1 = 18
GPIO.setup(SERVO_PIN_1, GPIO.OUT)
servo_pwm_1 = GPIO.PWM(SERVO_PIN_1, 50)
servo_pwm_1.start(7.0)

# Configure servo for horizontal camera movement
SERVO_PIN_2 = 23
GPIO.setup(SERVO_PIN_2, GPIO.OUT)
servo_pwm_2 = GPIO.PWM(SERVO_PIN_2, 50)
servo_pwm_2.start(7.0)

# Create new folder for picture and name it with date and time
dir_name = f"./kuvat_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
os.mkdir(dir_name)

# Assistance variables for handling pictures
pictureOnView = 0
changePicture = 0
takePicture = 0
lastPictureINdex = 0

# Configure camera and set resolution for video streaming
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)



# Function to take one high resolution picture, returns that picture encoded in base64.
def takeQualityPicture():
    try:
        global lastPictureINdex, pictureOnView, currentDir  # Importing allready existing variables to this method
        print("Taking high resolution picture...")

        # Setting resolution higher for one good picture
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # The camera returns two values: ret, which indicates whether capturing the picture was successful, and frame, which is the image data.
        # Save taken picture into folder, with correct index in name. Format is JPG.
        (ret, frame) = cap.read()
        lastPictureINdex += 1
        pictureOnView = lastPictureINdex
        imagePath = f"{dir_name}/qualityPicture{lastPictureINdex}.jpg"
        cv2.imwrite(imagePath, frame)

        # Setting resolution back to lower resolution for videosteam
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # Open image and encode it into base64 and retutn encoden image
        with open(imagePath, "rb") as image_file:
            encoded_picture = base64.b64encode(image_file.read()).decode('utf-8')
            print(f"Picture saved as: {imagePath}")
            return encoded_picture

    except Exception as e:
        print(f"Error with high resolution picture: {e}")


# Send already taken picture from server. All previous pictures are saved in same folder.
def sendRecentPicture(direction):
    global pictureOnView, lastPictureINdex # Import global variables needed here

    pictureOnView += direction # Change value of variable for tracking wich picture is currently displayed

    #  Check boundaries, if user is requesting pictures outside the valid index range
    if pictureOnView < 1:
        pictureOnView = 1                   # No picture before the first one
    elif pictureOnView > lastPictureINdex:
        pictureOnView = lastPictureINdex    # No picture after the last one

    # Fetch wanted picture and send it encoded to UI
    try:
        imagePath = f"{dir_name}/qualityPicture{pictureOnView}.jpg"
        with open(imagePath, "rb") as image_file:
            encoded_picture = base64.b64encode(image_file.read()).decode('utf-8')
            print(f"Showing qualityPicture{pictureOnView}")
            return encoded_picture
    except Exception as e:
        print(f"Error loading picture: {e}")
        return None


# Drive servo
def driveServo(camTurning):
    duty_cycle_1 = (7.0 - camTurning['x'] * 0.8)  # Neutral is 7% duty cycle
    servo_pwm_1.ChangeDutyCycle(duty_cycle_1)

    duty_cycle_2 = (7.0 + camTurning['y'] * 0.8)  # Neutral is 7% duty cycle
    servo_pwm_2.ChangeDutyCycle(duty_cycle_2)


# Send pictures or images.
async def send_image(websocket, path):
    print("Video streaming started")
    try:
        # Open camera
        while cap.isOpened():
            global takePicture, changePicture, pictureOnView  # Importing allready existing variables to this method

            # Take one higher resolution picture and send it to UI
            if takePicture == 1:
                await websocket.send(json.dumps({
                    "type": "quality",
                    "data": takeQualityPicture()
                }))
                takePicture = 0  # Reset flag

            # Fetch previously taken, higher resolution picture with one higher index and send it to UI
            elif changePicture == 1:
                print("next")
                await websocket.send(json.dumps({
                "type": "quality",
                "data": sendRecentPicture(1)
                }))
                changePicture = 0 # Reset flag

           # Fetch previously taken, higher resolution picture with one lower index and send it to UI
            elif changePicture == -1:
                print("Previous")
                await websocket.send(json.dumps({
                "type": "quality",
                "data": sendRecentPicture(-1)
                }))
                changePicture = 0 # Reset flag

            # If user is not asking for any quality picture, shoot and send lowerquality videoframe
            else:
                (ret, frame) = cap.read()
                _, buffer = cv2.imencode('.jpg', frame)
                encoded_frame = base64.b64encode(buffer).decode('utf-8')
                await websocket.send(json.dumps({
                    "type": "video",
                    "data": encoded_frame
                }))

            #print(f"take: {takePicture}, change: {changePicture}, onview: {pictureOnView}")
            await asyncio.sleep(1 / 25)  # Adjust FPS as needed

    except Exception as e:
        print(f"Streaming error: {e}")
        
    # Finally close camera
    finally:
        cap.release()
        print("Video streaming stopped")


# Handling data coming from UI
async def handler(websocket, path):
    print("Server started, waiting for data")
    async for message in websocket:
        try:
            global takePicture, changePicture   # Import global variables for use in in this function
            data = json.loads(message)          # Decode the JSON data received from UI

            var1 = data.get('var1', 0.0)                                # Driving left, value is 1 or 0
            var2 = data.get('var2', 0.0)                                # Driving right, value is 1 or 0
            joystick = data.get('joystick', {"x": 0.0, "y": 0.0})       # Joystick data separated into to two variables vary between -100 and 100
            camTurning = data.get('camTurning', {"x": 0, "y": 0})       # Direction of cameramovement separated in two variable, values are -1, 0 or 1
            takePicture= data.get('var4', 0)                            # Command for taking one higher resolution picture, value is 1 or 0
            changePicture = data.get('var5', 0)                         # Command for sending previous picture, value is -1 (previous), 0 (same) or 1 (next)

            # Below is debugging line
            #print(f"Button 1: {var1}, Button 2: {var2}, Joystick Position: x={joystick['x']}, y={joystick['y']}, camTurning: {camTurning['x']}, {camTurning['y']}, taking picture: {takePicture}, changePicture: {changePicture}")

            # Form a string of motorcontrolling variables
            arduino_data = str(f"{var1};{var2};{joystick['x']};{joystick['y']}x;")

            # Send data to Arduino via serial
            ser.dtr = False
            ser.rts = False
            ser.write(bytes(arduino_data, "UTF-8"))
            ser.flush()
 
            # Drive servo according to data from UI
            driveServo(camTurning)

        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Error: {e}")

# Start program. IP 0.0.0.0 means that servers can be accessed from all IPs in same WLAN
print("starting...")
start_handler = websockets.serve(handler, "0.0.0.0", 65432)     # Configure controlling server
start_stream = websockets.serve(send_image, "0.0.0.0", 65433)   # Configure video/pictures sending server into differrent port

# Start servers and run them forever
asyncio.get_event_loop().run_until_complete(asyncio.gather(start_handler, start_stream))
asyncio.get_event_loop().run_forever()


