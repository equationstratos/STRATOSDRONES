/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Parts Manager
===================================================== */


let droneParts = [];

let selectedPart = null;




/* =====================================================
                 INIT
===================================================== */


function initPartsManager(){


    console.log(
        "Parts Manager initialized"
    );


    createAllParts();


}







/* =====================================================
             CREATE ALL COMPONENTS
===================================================== */


function createAllParts(){



    createPart(
        "FRAME",
        "frame",
        -80,
        0,
        -40
    );



    createPart(
        "FLIGHT CONTROLLER",
        "fc",
        0,
        5,
        -40
    );



    createPart(
        "ESC",
        "esc",
        30,
        5,
        -40
    );



    createPart(
        "VTX",
        "vtx",
        60,
        5,
        -40
    );



    createPart(
        "ELRS RX",
        "rx",
        -60,
        5,
        40
    );



    createPart(
        "GPS",
        "gps",
        0,
        5,
        40
    );



    createPart(
        "BUZZER",
        "buzzer",
        40,
        5,
        40
    );



    createPart(
        "CAPACITOR",
        "capacitor",
        80,
        5,
        40
    );




    for(let i=0;i<4;i++)
    {


        createPart(

            "MOTOR "+(i+1),

            "motor",

            -100+i*50,

            10,

            100

        );


    }




    createPart(

        "BATTERY",

        "battery",

        0,

        5,

        120

    );



}









/* =====================================================
               CREATE OBJECT
===================================================== */


function createPart(

name,

type,

x,

y,

z

){



    let geometry;



    switch(type)

    {


        case "motor":

        geometry =
        new THREE.CylinderGeometry(
            8,
            8,
            8,
            32
        );

        break;




        case "battery":

        geometry =
        new THREE.BoxGeometry(
            30,
            10,
            15
        );

        break;




        case "frame":

        geometry =
        new THREE.BoxGeometry(
            60,
            5,
            60
        );

        break;




        default:

        geometry =
        new THREE.BoxGeometry(
            20,
            5,
            20
        );


    }







    let material =
    new THREE.MeshStandardMaterial({

        color:
        0x555555,


        roughness:
        .6

    });





    let mesh =
    new THREE.Mesh(

        geometry,

        material

    );



    mesh.castShadow=true;



    mesh.position.set(

        x,

        y,

        z

    );



    mesh.userData={

        name:name,

        type:type,

        installed:false


    };





    scene.add(mesh);



    droneParts.push(mesh);



}









/* =====================================================
              SORT ON ENGINEER MAT
===================================================== */


function sortPartsOnBench(){



    console.log(

        "Arranging parts..."

    );



    droneParts.forEach(

        (part,index)=>{


            let column =
            index % 5;


            let row =
            Math.floor(
                index / 5
            );



            let targetX =
            -120 + column*60;



            let targetZ =
            -50 + row*60;





            animatePartMove(

                part,

                targetX,

                5,

                targetZ

            );



        }


    );



}









/* =====================================================
                MOVE ANIMATION
===================================================== */


function animatePartMove(

object,

x,

y,

z

){



    let start =
    object.position.clone();



    let target =
    new THREE.Vector3(

        x,

        y,

        z

    );



    let progress=0;



    function move(){



        progress +=0.03;



        object.position.lerpVectors(

            start,

            target,

            progress

        );



        if(progress<1)

        {

            requestAnimationFrame(move);

        }



    }



    move();



}









/* =====================================================
               SELECT PART
===================================================== */


function selectPart(part){


    selectedPart =
    part;


    console.log(

        "Selected:",

        part.userData.name

    );


}








window.initPartsManager =
initPartsManager;


window.sortPartsOnBench =
sortPartsOnBench;


window.selectPart =
selectPart;
