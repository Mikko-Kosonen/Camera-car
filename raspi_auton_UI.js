
// JavaScript file to handle frontend logic. 
// Buttons and joystick functionality, showing video and higher resolution pictures, sending data gathered from user's actions to server. 
// Runs on user's device.


// Change IP-address to match to IP of Raspberry Pi. Crucial for functionality!
const IP = "192.168.188.233";

// Create a WebSocket connections for sending commands and receiving video/pictures
const handlerSocket = new WebSocket("ws://"+IP+":65432");
const videoSocket = new WebSocket("ws://"+IP+":65433");

// Create joystick
const joystick = createJoystick(document.getElementById('wrapper'));



// Eventhandler for videoSocket. Executed when received message.
videoSocket.onmessage = (event) => {
  // Parse the incoming message as JSON
  const message = JSON.parse(event.data);

  // Check if message type suggests message to contain videoframe or a quality picture. 
  // If quality or video, update corresponding container on UI. In other cases, logs warning.
  if (message.type === "quality") {
    const img = document.getElementById("qualityPicture");
    img.src = "data:image/jpeg;base64," + message.data;
    console.log("High-quality picture received.");
  } 
  else if (message.type === "video") {
    const img = document.getElementById("videoStream");
    img.src = "data:image/jpeg;base64," + message.data;
  } 
  else {
    console.warn("Unknown message type:", message.type);
  }
};



// Eventhandler for handlerSocket. Executed when connection between server and UI is opened.
handlerSocket.addEventListener("open", () => {
  console.log("HandlerSocket connection opened!");

  // Infinite loop to send data to server in every 100ms.
  setInterval(() => {

    // Get data from buttons and joystick.
    const joystickPosition = joystick.getPosition();
    const camTurningx = - buttonStates['camLeft'] + buttonStates['camRight'];
    const camTurningy = - buttonStates['camDown'] + buttonStates['camUp'];
    const changePicture = -buttonStates['previousPic'] + buttonStates['nextPic']

    // Create a data object to send
    const data = {
      var1: buttonStates['vasen'],          // Command for driving left, value is 1 or 0
      var2: buttonStates['oikea'],          // Command for driving right, value is 1 or 0
      joystick: {
        x: joystickPosition.x,              // X-coordinate of joystick, vary between -100 and 100
        y: -joystickPosition.y,             // Y-coordinate of joystick, vary between -100 and 100
      },  
      camTurning: {
        x: camTurningx,                     // Command for turning camera horizontally, values are -1, 0 or 1
        y: camTurningy,                     // Command for turning camera vertically, values are -1, 0 or 1
      },
      var4: buttonStates['takePicture'],    // Command for taking one higher resolution picture, value is 1 or 0
      var5: changePicture                   // Command for sending previous picture, value is -1 (previous), 0 (same) or 1 (next)
    };

    // Send the data as a JSON string
    handlerSocket.send(JSON.stringify(data));

    // Reset flags
    buttonStates['takePicture'] = 0;
    buttonStates['previousPic'] = 0;
    buttonStates['nextPic'] = 0;

  }, 100);  // 100ms delay
});

// Stop sending data when the socket is closed
handlerSocket.addEventListener("close", () => {
  clearInterval(intervalId); // Stop sending data when the socket is closed
  console.log("HandlerSocket connection closed!");
});



// Joystick code is adapted from https://jsfiddle.net/aa0et7tr/5/, with a few modifications to meet our requirements.
function createJoystick(parent) {
  const maxDiff = 100;
  const stick = document.createElement('div');
  stick.classList.add('joystick');

  // Add joystick to have EventListeners for user's actions.
  stick.addEventListener('mousedown', handleMouseDown);
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
  stick.addEventListener('touchstart', handleMouseDown);
  document.addEventListener('touchmove', handleMouseMove);
  document.addEventListener('touchend', handleMouseUp);

  // Starting position
  let dragStart = null;
  let currentPos = { x: 0, y: 0 };


  function handleMouseDown(event) {
    stick.style.transition = '0s';
    if (event.changedTouches) {
      // For touch events, use the first touch point's coordinates
      dragStart = {
        x: event.changedTouches[0].clientX,
        y: event.changedTouches[0].clientY,
      };
      return;
    }
    // For mouse events, use the mouse coordinates
    dragStart = {
      x: event.clientX,
      y: event.clientY,
    };

  }
  
  // While user is pressing joystick, move sphere along with mouse or finger.
  function handleMouseMove(event) {
    if (dragStart === null) return;
    event.preventDefault(); // Prevent default behavior to ensure smooth dragging
    
    if (event.changedTouches) {
      event.clientX = event.changedTouches[0].clientX;
      event.clientY = event.changedTouches[0].clientY;
    }
    // The difference between the current position and the drag start position
    const xDiff = event.clientX - dragStart.x;
    const yDiff = event.clientY - dragStart.y;

    // Limit the joystick movement within the maximum allowed range
		const xNew = Math.min(Math.max(xDiff, -100), 100);
		const yNew = Math.min(Math.max(yDiff, -100), 100)

    // Update the joystick's visual position using CSS transform and then the current position
    stick.style.transform = `translate3d(${xNew}px, ${yNew}px, 0px)`;
    currentPos = { x: xNew, y: yNew };
  }

  // Reset the joystick to its initial position when released
  function handleMouseUp(event) {
    if (dragStart === null) return;
      stick.style.transition = '.2s';                           // Add a smooth transition when resettingz
      stick.style.transform = `translate3d(0px, 0px, 0px)`;     // Reset joystick position to center
      dragStart = null;
      currentPos = { x: 0, y: 0 };
  }

  // Append the joystick element to the specified parent element
  parent.appendChild(stick);

  // Return an object with a method to get the current joystick position
  return {
    getPosition: () => currentPos,
  };
}



// Get buttons from the main HTML element. Create an object called ButtonStates to store values of buttons, linked with corresponding names.
const buttons = document.querySelectorAll('#main button');
const buttonStates = {};

// Set every button to have eventListener for user's clickings (or touches if on mobile device).
// If working with pictures, change value only when releasing button. Otherwise server would get, for example, request to take higher resolution pictures while pressing "take picture" button.
buttons.forEach(button => {
  buttonStates[button.id] = 0;

  if ((button.id !== 'takePicture') && (button.id !== 'previousPic') && (button.id !== 'nextPic')){
    button.addEventListener('mousedown', () => {buttonStates[button.id] = 1;});
    button.addEventListener('touchstart', () => {buttonStates[button.id] = 1;});

    button.addEventListener('mouseup', () => {buttonStates[button.id] = 0;});
    button.addEventListener('touchend', () => {buttonStates[button.id] = 0;});
  }

  else if ((button.id === 'takePicture') || (button.id === 'previousPic') || (button.id === 'nextPic')){
    button.addEventListener('mouseup', () =>{buttonStates[button.id] = 1;})
    button.addEventListener('touchend', () =>{buttonStates[button.id] = 1;})
  }

});



