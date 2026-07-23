/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Audio Engine
===================================================== */


let audioContext;

let audioReady=false;






/* =====================================================
                INIT AUDIO
===================================================== */


function initAudio(){



    try{


        audioContext =
        new (
            window.AudioContext ||
            window.webkitAudioContext
        )();



        audioReady=true;



        console.log(

            "Audio system ready"

        );


    }


    catch(error)

    {


        console.warn(

            "Audio unavailable"

        );


    }



}









/* =====================================================
              CREATE TONE
===================================================== */


function playTone(

frequency,

duration,

type="sine"

){



    if(!audioReady)
    return;



    let oscillator =
    audioContext.createOscillator();



    let gain =
    audioContext.createGain();




    oscillator.type =
    type;



    oscillator.frequency.value =
    frequency;



    oscillator.connect(
        gain
    );


    gain.connect(

        audioContext.destination

    );



    gain.gain.value =
    0.1;



    oscillator.start();



    setTimeout(()=>{


        oscillator.stop();


    },duration);



}









/* =====================================================
              ESC BEEP
===================================================== */


function playESCBeep(){



    playTone(

        880,

        150,

        "square"

    );



    setTimeout(()=>{


        playTone(

            1100,

            150,

            "square"

        );


    },200);



}









/* =====================================================
              BOOT SOUND
===================================================== */


function playBootSound(){



    playTone(

        500,

        200

    );



    setTimeout(()=>{


        playTone(

            700,

            200

        );


    },250);



    setTimeout(()=>{


        playTone(

            900,

            300

        );


    },500);



}









/* =====================================================
              MOTOR START
===================================================== */


function playMotorSound(){



    if(!audioReady)
    return;



    let oscillator =
    audioContext.createOscillator();



    let gain =
    audioContext.createGain();



    oscillator.type =
    "sawtooth";



    oscillator.frequency.value =
    80;



    oscillator.connect(
        gain
    );



    gain.connect(

        audioContext.destination

    );



    gain.gain.value =
    0.05;



    oscillator.start();




    let frequency=80;



    let interval =
    setInterval(()=>{


        frequency +=50;


        oscillator.frequency.value =
        frequency;



    },100);




    setTimeout(()=>{


        clearInterval(
            interval
        );


        oscillator.stop();



    },2500);



}








/* =====================================================
              SOLDER SOUND
===================================================== */


function playSolderSound(){



    playTone(

        2000,

        80,

        "triangle"

    );



}








/* =====================================================
              ERROR SOUND
===================================================== */


function playErrorSound(){



    playTone(

        120,

        700,

        "sawtooth"

    );



}









window.initAudio =
initAudio;


window.playESCBeep =
playESCBeep;


window.playBootSound =
playBootSound;


window.playMotorSound =
playMotorSound;


window.playSolderSound =
playSolderSound;


window.playErrorSound =
playErrorSound;
