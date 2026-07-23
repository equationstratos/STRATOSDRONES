/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Configuration File
===================================================== */


/*
    GLOBAL CONFIG
*/


const STRATOS_CONFIG = {


    droneName:
    "TinyHoop MK1",



    manufacturer:
    "STRATOS DRONES",



    version:
    "BUILD SIMULATOR 1.0",



    modelPath:
    "../models/tinyhoop_mk1.glb",




/* =====================================================
              BUILD STEPS
===================================================== */


buildSteps:[


{
id:1,

name:"Prepare Frame",

description:
"Place the main carbon frame on the engineer mat",

part:"frame"

},



{
id:2,

name:"Install Motors",

description:
"Install the four brushless motors",

part:"motor"

},



{
id:3,

name:"Install Flight Stack",

description:
"Mount FC and ESC stack",

part:"stack"

},



{
id:4,

name:"Install Camera",

description:
"Install FPV camera",

part:"camera"

},



{
id:5,

name:"Install VTX",

description:
"Install video transmitter",

part:"vtx"

},



{
id:6,

name:"Install Receiver",

description:
"Install ELRS receiver",

part:"rx"

},



{
id:7,

name:"Install GPS",

description:
"Install GPS module",

part:"gps"

},



{
id:8,

name:"Solder Electronics",

description:
"Connect all electrical points",

part:"solder"

},



{
id:9,

name:"Final Assembly",

description:
"Close the drone",

part:"finish"

}


],




/* =====================================================
                  PARTS DATABASE
===================================================== */


parts:{



frame:{


name:
"Carbon Frame",


category:
"mechanical",


required:true,


position:

{
x:0,
y:0,
z:0
}


},




motor:{


name:
"Brushless Motor",


category:
"mechanical",


quantity:4,


required:true


},





fc:{


name:
"Flight Controller",


category:
"electronics",


required:true


},





esc:{


name:
"ESC Board",


category:
"electronics",


required:true


},




camera:{


name:
"FPV Camera",


category:
"electronics",


required:true


},




vtx:{


name:
"Video Transmitter",


category:
"electronics",


required:true


},




rx:{


name:
"ELRS Receiver",


category:
"electronics",


required:true


},




gps:{


name:
"GPS Module",


category:
"electronics",


required:false


},





buzzer:{


name:
"Lost Drone Buzzer",


category:
"electronics",


required:false


},





capacitor:{


name:
"Low ESR Capacitor",


category:
"electronics",


required:true


},





battery:{


name:
"2S/3S LiPo Battery",


category:
"power",


required:true


}


},





/* =====================================================
             SOLDER POINT DATABASE
===================================================== */


solderPoints:{



FC_5V:{

component:"FC",

pad:"5V",

position:
{x:0,y:10}

},



FC_GND:{

component:"FC",

pad:"GND",

position:
{x:-10,y:10}

},



FC_TX:

{

component:"FC",

pad:"TX",

position:
{x:20,y:5}

},




FC_RX:

{

component:"FC",

pad:"RX",

position:
{x:25,y:5}

},




VTX_5V:

{

component:"VTX",

pad:"5V",

position:
{x:120,y:20}

},



VTX_GND:

{

component:"VTX",

pad:"GND",

position:
{x:120,y:0}

},



VTX_RX:

{

component:"VTX",

pad:"RX",

position:
{x:130,y:10}

},




RX_TX:

{

component:"ELRS",

pad:"TX",

position:
{x:-100,y:20}

},




RX_GND:

{

component:"ELRS",

pad:"GND",

position:
{x:-100,y:0}

}


},






/* =====================================================
              ELECTRONIC CONNECTIONS
===================================================== */


wires:[



{

from:
"FC_5V",

to:
"VTX_5V",

type:
"power"

},



{

from:
"FC_GND",

to:
"VTX_GND",

type:
"ground"

},



{

from:
"FC_TX",

to:
"RX_TX",

type:
"uart"

},



{

from:
"FC_TX",

to:
"VTX_RX",

type:
"smart_audio"

}



],






/* =====================================================
                 TEST SEQUENCE
===================================================== */


testSequence:[


"Battery connected",

"Voltage check",

"ESC initialization",

"Gyroscope calibration",

"Receiver signal",

"Camera signal",

"VTX transmission",

"Motor spin test",

"ARM READY"


]



};





// Export global

window.STRATOS_CONFIG =
STRATOS_CONFIG;
