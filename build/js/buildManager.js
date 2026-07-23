/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Assembly Manager FIXED
===================================================== */


let currentStep = 0;

let assemblyStarted = false;





function initBuildManager(){


    console.log(
        "Build Manager ready"
    );


    currentStep = 0;

    assemblyStarted = false;


}









function startAssembly(){


    if(assemblyStarted)

    return;



    assemblyStarted=true;

    currentStep=0;



    updateStatus(

        "BUILD START",

        "Preparing engineering bench..."

    );



    setTimeout(()=>{

        explodeDrone();


    },500);


}









function explodeDrone(){



    console.log(

        "Exploding drone"

    );



    updateStatus(

        "DISASSEMBLED",

        "Components sorted on engineer mat"

    );




    /*
       IMPORTANT
       Use partsManager system
    */


    if(

        window.sortPartsOnBench

    )

    {


        sortPartsOnBench();


    }

    else

    {

        console.warn(

            "Parts sorter missing"

        );

    }





    setTimeout(()=>{


        nextBuildStep();


    },1500);



}









function nextBuildStep(){



    if(

        typeof STRATOS_CONFIG === "undefined"

    )

    {

        console.warn(

            "Config missing"

        );


        return;

    }





    if(

        currentStep >= STRATOS_CONFIG.buildSteps.length

    )

    {


        finishAssembly();


        return;


    }






    let step =

    STRATOS_CONFIG.buildSteps[currentStep];





    updateStatus(

        "STEP "+step.id+" : "+step.name,

        step.description

    );





    updateProgress(

        step.id

    );



    currentStep++;


}









function finishAssembly(){


    updateStatus(

        "BUILD COMPLETE",

        "Ready for drone test"

    );



    updateProgress(

        100

    );


}









function updateProgress(value){



    let bar =

    document.getElementById(

        "progress"

    );



    if(!bar)

    return;



    bar.style.width =

    value+"%";



}









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









window.initBuildManager =
initBuildManager;


window.startAssembly =
startAssembly;


window.resetBuild =
resetBuild;


window.nextBuildStep =
nextBuildStep;
