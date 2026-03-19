import processing.serial.*;
import java.util.HashMap;


float x, y, yaw, ir0, ir1, ir2, ir3, ir4, ir5, ir6, ir7, ir8, x_set, y_set, state, end_t, SOC;

HashMap<String, Float> values = new HashMap<String, Float>();

Serial myPort;

String portName = "/dev/tty.usbserial-0001";
int baud = 115200;

PImage gameTrack;

float scaleFactor = 0.0;

void setup(){
  fullScreen();
  pixelDensity(displayDensity());
  
  scaleFactor = 1500.0/1800.0;
  
  try {
    myPort = new Serial(this, portName, baud);
  } catch (Exception e) {
    println("Failed to open serial port: " + portName);
    println("Error: " + e);
    exit();
  }
  
  println("Opened: " + portName + " @ " + baud);
  
  gameTrack = loadImage("GameTrack.png");
}

void keyPressed() {
  myPort.write(key);
}

void draw(){
  background(255);
  image(gameTrack, 0, 115, 1512, 751);
  
  pushMatrix();
  translate(0, 115 + 751);
  scale(scaleFactor, -scaleFactor);
  
  fill(255,0,0,125);
  stroke(255,0,0);
  
  ellipseMode(CENTER);
  ellipse(x,y,165,165);
  
  stroke(0,255,0);
  line(x, y , x + 150*cos(yaw), y + 150*sin(yaw));
  
  stroke(0);
  fill(((ir0 * -1) + 100) * 2.55);
  rect(450,-100,100,100);
  fill(((ir1 * -1) + 100) * 2.55);
  rect(550,-100,100,100);
  fill(((ir2 * -1) + 100) * 2.55);
  rect(650,-100,100,100);
  fill(((ir3 * -1) + 100) * 2.55);
  rect(750,-100,100,100);
  fill(((ir4 * -1) + 100) * 2.55);
  rect(850,-100,100,100);
  fill(((ir5 * -1) + 100) * 2.55);
  rect(950,-100,100,100);
  fill(((ir6 * -1) + 100) * 2.55);
  rect(1050,-100,100,100);
  fill(((ir7 * -1) + 100) * 2.55);
  rect(1150,-100,100,100);
  fill(((ir8 * -1) + 100) * 2.55);
  rect(1250,-100,100,100);
  
  stroke(0,0,255);
  fill(0,0,255,200);
  if(x_set != 0 && y_set != 0){
    ellipse(x_set, y_set, 25, 25);
  }
  
  popMatrix();
  
  fill(0);
  textSize(50);
  text("State: " + str(int(state)), 100,100);
  text("End time: " + nf(end_t,2,2), 330,100);
  text("Yaw: " + nf(yaw,3,1), 700,100);
  text("Battery: " + int(SOC) + "%", 1030,100);
}


void serialEvent(Serial p) {
  String line = p.readStringUntil('\n');
  if (line == null) return;
  line = trim(line);
  if (line.length() == 0) return;
  
  int eqIndex = line.indexOf('=');
  if (eqIndex < 0) {
    println("Invalid line: " + line);
    return;
  }

  String key = trim(line.substring(0, eqIndex));
  String valueStr = trim(line.substring(eqIndex + 1));

  try {
    float value = Float.parseFloat(valueStr);

    // Store in generic map
    values.put(key, value);

    // Update specific variables
    if (key.equals("x")) {
      x = value;
    } else if (key.equals("y")) {
      y = value;
    } else if (key.equals("yaw")) {
      yaw = value;
    } else if (key.equals("ir0")) {
      ir0 = value;
    } else if (key.equals("ir1")) {
      ir1 = value;
    } else if (key.equals("ir2")) {
      ir2 = value;
    } else if (key.equals("ir3")) {
      ir3 = value;
    } else if (key.equals("ir4")) {
      ir4 = value;
    } else if (key.equals("ir5")) {
      ir5 = value;
    } else if (key.equals("ir6")) {
      ir6 = value;
    } else if (key.equals("ir7")) {
      ir7 = value;
    } else if (key.equals("ir8")) {
      ir8 = value;
    } else if (key.equals("x_set")) {
      x_set = value;
    } else if (key.equals("y_set")) {
      y_set = value;
    } else if (key.equals("state")) {
      state = value;
    } else if (key.equals("end_t")) {
      end_t = value;
    } else if (key.equals("SOC")) {
      SOC = value;
    }

  } catch (NumberFormatException e) {
    println("Could not parse float from: " + line);
  }
}
