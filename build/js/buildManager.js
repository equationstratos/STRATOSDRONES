/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Assembly Manager
===================================================== */


let currentStep = 0;

let assemblyStarted = false;

let assemblyParts = [];





/* =====================================================
              INITIALISATION
===================================================== */


function initBuildManager(){


    console.log(
        "Build Manager ready"
    );


    currentStep = 0;

    assemblyStarted = false;


}








/* =====================================================
                 START BUILD
===================================================== */


function startAssembly(){


    if(assemblyStarted)
    return;



    assemblyStarted = true;



    currentStep = 0;



    updateStatus(

        "BUILD START",

        "Preparing engineering bench..."

    );




    setTimeout(()=>{


        explodeDrone();



    },500);




}









/* =====================================================
              EXPLODE VIEW
===================================================== */


function explodeDrone(){



    updateStatus(

        "DISASSEMBLED",

        "Components sorted on engineer mat"

    );



    console.log(

        "Exploding drone"

    );




    if(window.sortPartsOnBench)

    {


        sortPartsOnBench();


    }





    setTimeout(()=>{


        nextBuildStep();


    },2000);



}









/* =====================================================
                BUILD STEPS
===================================================== */


function nextBuildStep(){



    if(currentStep >= STRATOS_CONFIG.buildSteps.length)

    {


        finishAssembly();


        return;


    }





    let step =
    STRATOS_CONFIG.buildSteps[currentStep];





    updateStatus(

        "STEP "
        +
        step.id
        +
        " : "
        +
        step.name,


        step.description


    );





    updateProgress(

        step.id

    );




    currentStep++;




}









/* =====================================================
             COMPLETE BUILD
===================================================== */


function finishAssembly(){



    updateStatus(

        "BUILD COMPLETE",

        "Ready for drone test"

    );



    updateProgress(

        100

    );


}









/* =====================================================
               PROGRESS BAR
===================================================== */


function updateProgress(value){



    let bar =
    document.getElementById(

        "progress"

    );



    if(!bar)
    return;




    let percent;



    if(value <= 10)

    {

        percent =
        value * 10;

    }

    else

    {

        percent =
        value;

    }



    bar.style.width =
    percent
    +
    "%";



}









/* =====================================================
                 RESET
===================================================== */


function resetBuild(){



    console.log(

        "Reset build"

    );



    currentStep=0;


    assemblyStarted=false;



    updateProgress(0);



    updateStatus(

        "READY",

        "Press BUILD to start assembly"

    );



}









/* =====================================================
             WORKSHOP SORT
===================================================== */


function sortPartsOnBench(){



    /*
        Future connection
        with partsManager.js

    */


    console.log(

        "Sorting components..."

    );



    let positions=[



        {
            name:"FRAME",
            x:-80,
            z:-50
        },


        {
            name:"ELECTRONICS",
            x:0,
            z:-50
        },


        {
            name:"MOTORS",
            x:80,
            z:-50
        },


        {
            name:"BATTERY",
            x:0,
            z:80
        }


    ];



    console.log(

        positions

    );


}








/* =====================================================
EXPORT
===================================================== */


window.initBuildManager =
initBuildManager;


window.startAssembly =
startAssembly;


window.resetBuild =
resetBuild;


window.nextBuildStep =
nextBuildStep;
