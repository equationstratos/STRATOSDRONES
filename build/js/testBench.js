/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Drone Test Bench
===================================================== */


let testRunning=false;

let testSuccess=false;



/* =====================================================
              INIT
===================================================== */


function initTestBench(){


    console.log(
        "Test bench ready"
    );


}








/* =====================================================
              START TEST
===================================================== */


function startTest(){



    if(testRunning)
    return;



    testRunning=true;



    let panel =
    document.getElementById(
        "testPanel"
    );



    if(panel)

    panel.style.display =
    "block";




    let log =
    document.getElementById(
        "testLog"
    );



    if(log)

    log.innerHTML="";




    runSequence();



}








/* =====================================================
              TEST SEQUENCE
===================================================== */


function runSequence(){



    let sequence =
    STRATOS_CONFIG.testSequence;



    let index=0;



    function next(){



        if(index >= sequence.length)

        {


            finishTest();


            return;


        }





        addTestLine(

            sequence[index]

        );



        index++;



        setTimeout(

            next,

            1000

        );



    }



    next();



}








/* =====================================================
              LOG
===================================================== */


function addTestLine(text){



    let log =
    document.getElementById(
        "testLog"
    );



    if(log)

    {


        log.innerHTML +=

        "> "
        +
        text
        +
        "<br>";



        log.scrollTop =
        log.scrollHeight;


    }



}









/* =====================================================
              FINAL CHECK
===================================================== */


function finishTest(){



    let solderOK =
    checkSolderComplete();



    if(solderOK)

    {


        droneStartup();



    }

    else

    {


        droneFailure();



    }



}









/* =====================================================
              SUCCESS
===================================================== */


function droneStartup(){



    testSuccess=true;



    addTestLine(

        "SYSTEM READY"

    );



    addTestLine(

        "ARMING..."

    );



    setTimeout(()=>{


        addTestLine(

            "MOTOR SPIN TEST"

        );



        if(window.playMotorSound)

        {

            playMotorSound();

        }



    },1000);





    setTimeout(()=>{


        addTestLine(

            "✔ BUILD SUCCESSFUL"

        );



        updateStatus(

            "DRONE READY",

            "Successful first power up"

        );



        testRunning=false;



    },3000);



}









/* =====================================================
              FAILURE
===================================================== */


function droneFailure(){



    addTestLine(

        "ERROR"

    );



    addTestLine(

        "SHORT CIRCUIT DETECTED"

    );



    updateStatus(

        "FAILURE",

        "Check wiring"

    );



    if(window.showSmoke)

    {

        showSmoke();

    }



    testRunning=false;



}









/* =====================================================
              CLOSE PANEL
===================================================== */


document.addEventListener(

"DOMContentLoaded",

()=>{


let close =
document.getElementById(
"closeTest"
);



if(close)

{

close.onclick=()=>{


document.getElementById(
"testPanel"
).style.display="none";


};



}



});








window.initTestBench =
initTestBench;


window.startTest =
startTest;
