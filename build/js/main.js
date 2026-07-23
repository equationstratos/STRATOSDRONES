/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Main Controller
===================================================== */


let simulatorReady = false;



/* =====================================================
                 START APPLICATION
===================================================== */


window.addEventListener(

"DOMContentLoaded",

()=>{


    console.log(

        "STRATOS TinyHoop Builder starting..."

    );



    initializeBuilder();



});








function initializeBuilder(){



    /*
        Create 3D environment
    */


    initScene();





    /*
        Load drone if available
    */


    loadDroneModel();





    /*
        Initialize systems
    */


    if(window.initPartsManager)
    {

        initPartsManager();

    }



    if(window.initBuildManager)
    {

        initBuildManager();

    }



    if(window.initSnapSystem)
    {

        initSnapSystem();

    }



    if(window.initWiring)
    {

        initWiring();

    }



    if(window.initSolderMode)
    {

        initSolderMode();

    }



    if(window.initTestBench)
    {

        initTestBench();

    }



    if(window.initAudio)
    {

        initAudio();

    }



    if(window.initUI)
    {

        initUI();

    }





    simulatorReady=true;



    updateStatus(

        "READY",

        "Press BUILD to start assembly"

    );



}









/* =====================================================
                  BUILD BUTTON
===================================================== */


function startBuild(){



    if(!simulatorReady)
    return;



    console.log(

        "Starting build mode"

    );



    updateStatus(

        "BUILD MODE",

        "Preparing engineer workshop..."

    );




    if(window.startAssembly)
    {

        startAssembly();

    }



}








/* =====================================================
                   RESET
===================================================== */


function resetSimulator(){



    console.log(

        "Reset simulator"

    );



    if(window.resetBuild)
    {

        resetBuild();

    }



    if(window.clearWires)
    {

        clearWires();

    }




    updateStatus(

        "RESET",

        "All components returned"

    );



}









/* =====================================================
                   TEST
===================================================== */


function runDroneTest(){



    console.log(

        "Starting drone test"

    );



    if(window.startTest)
    {

        startTest();

    }

    else
    {

        updateStatus(

            "TEST",

            "Test system not loaded"

        );

    }


}









/* =====================================================
                 STATUS DISPLAY
===================================================== */


function updateStatus(

title,

description

){



    const titleBox =
    document.getElementById(

        "stepTitle"

    );



    const descBox =
    document.getElementById(

        "stepDescription"

    );




    if(titleBox)

    titleBox.innerHTML =
    title;



    if(descBox)

    descBox.innerHTML =
    description;



}









/* =====================================================
                BUTTON EVENTS
===================================================== */


function connectMainButtons(){



    const build =
    document.getElementById(

        "buildButton"

    );


    const reset =
    document.getElementById(

        "resetButton"

    );


    const test =
    document.getElementById(

        "testButton"

    );




    if(build)

    {

        build.onclick =
        startBuild;

    }





    if(reset)

    {

        reset.onclick =
        resetSimulator;

    }





    if(test)

    {

        test.onclick =
        runDroneTest;

    }



}






/*
    Connect when page loaded
*/


window.addEventListener(

"load",

()=>{


    connectMainButtons();


});








/* =====================================================
                  GLOBAL EXPORT
===================================================== */


window.startBuild =
startBuild;


window.resetSimulator =
resetSimulator;


window.runDroneTest =
runDroneTest;


window.updateStatus =
updateStatus;
