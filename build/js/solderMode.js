/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Soldering Mode System
===================================================== */


let solderActive = false;

let previousCameraPosition;

let previousTarget;

let solderObjects=[];





/* =====================================================
              INIT
===================================================== */


function initSolderMode(){


    console.log(
        "Solder mode ready"
    );


    const exit =
    document.getElementById(
        "exitSolder"
    );


    if(exit)

    {

        exit.onclick =
        exitSolderMode;

    }



}








/* =====================================================
              ENTER SOLDER MODE
===================================================== */


function enterSolderMode(){



    if(solderActive)
    return;



    solderActive=true;



    document.getElementById(
        "solderMode"
    ).style.display =
    "block";




    previousCameraPosition =
    camera.position.clone();



    previousTarget =
    controls.target.clone();




    isolateElectronics();



    moveCameraToBoard();



    enablePadSelection();



    updateStatus(

        "SOLDER MODE",

        "Connect electronic pads"

    );



}








/* =====================================================
              CAMERA ZOOM
===================================================== */


function moveCameraToBoard(){



    camera.position.set(

        0,

        160,

        0

    );



    controls.target.set(

        0,

        0,

        0

    );



    controls.update();



}









/* =====================================================
              ISOLATE COMPONENTS
===================================================== */


function isolateElectronics(){



    solderObjects=[];



    scene.traverse(

    object=>{


        if(object.isMesh)

        {



            let type =
            object.userData.type;



            if(

            type==="fc"

            ||

            type==="esc"

            ||

            type==="vtx"

            ||

            type==="rx"

            )


            {



                solderObjects.push(
                    object
                );



                object.visible=true;



            }

            else

            {


                if(
                object !== droneRoot
                )

                object.visible=false;


            }



        }



    });



}









/* =====================================================
              EXIT MODE
===================================================== */


function exitSolderMode(){



    solderActive=false;



    document.getElementById(
        "solderMode"
    ).style.display =
    "none";




    restoreScene();



    camera.position.copy(

        previousCameraPosition

    );



    controls.target.copy(

        previousTarget

    );



    controls.update();




    updateStatus(

        "BUILD MODE",

        "Continue assembly"

    );



}









/* =====================================================
              RESTORE OBJECTS
===================================================== */


function restoreScene(){



    scene.traverse(

    object=>{


        if(object.isMesh)

        {


            object.visible=true;


        }



    });



}









/* =====================================================
              FINISH CHECK
===================================================== */


function checkSolderComplete(){



    let required =
    STRATOS_CONFIG.wires.length;



    let made =
    solderConnections.length;



    if(made >= required)

    {


        updateStatus(

            "ELECTRONICS OK",

            "Ready for final test"

        );



        return true;

    }



    else

    {


        updateStatus(

            "MISSING WIRES",

            made+
            "/"+
            required

        );



        return false;


    }



}







window.initSolderMode =
initSolderMode;


window.enterSolderMode =
enterSolderMode;


window.exitSolderMode =
exitSolderMode;


window.checkSolderComplete =
checkSolderComplete;
