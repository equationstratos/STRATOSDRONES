/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Snap Assembly System
===================================================== */


let snapEnabled = false;

let raycaster;

let mouse;

let draggingPart = null;

let dragPlane;

let offset;






/* =====================================================
                INIT SNAP SYSTEM
===================================================== */


function initSnapSystem(){


    console.log(
        "Snap System ready"
    );



    raycaster =
    new THREE.Raycaster();



    mouse =
    new THREE.Vector2();



    dragPlane =
    new THREE.Plane(

        new THREE.Vector3(
            0,
            1,
            0
        ),

        0

    );



    offset =
    new THREE.Vector3();



    renderer.domElement.addEventListener(

        "pointerdown",

        pointerDown

    );



    renderer.domElement.addEventListener(

        "pointermove",

        pointerMove

    );



    renderer.domElement.addEventListener(

        "pointerup",

        pointerUp

    );



    snapEnabled=true;


}








/* =====================================================
                MOUSE DOWN
===================================================== */


function pointerDown(event){



    if(!snapEnabled)
    return;



    updateMouse(event);



    raycaster.setFromCamera(

        mouse,

        camera

    );



    let hits =
    raycaster.intersectObjects(

        droneParts,

        true

    );




    if(hits.length)

    {


        draggingPart =
        hits[0].object;



        if(
        draggingPart.userData
        )

        {


            selectPart(
                draggingPart
            );


            draggingPart.material.emissive =
            new THREE.Color(
                0x003366
            );


        }



    }




}









/* =====================================================
                DRAG MOVE
===================================================== */


function pointerMove(event){



    if(!draggingPart)
    return;



    updateMouse(event);



    raycaster.setFromCamera(

        mouse,

        camera

    );



    let point =
    new THREE.Vector3();



    raycaster.ray.intersectPlane(

        dragPlane,

        point

    );



    if(point)

    {


        draggingPart.position.x =
        point.x;



        draggingPart.position.z =
        point.z;



    }



}









/* =====================================================
                RELEASE
===================================================== */


function pointerUp(){



    if(!draggingPart)
    return;



    checkSnap(

        draggingPart

    );



    if(
    draggingPart.material.emissive
    )

    {

        draggingPart.material.emissive =
        new THREE.Color(
            0x000000
        );

    }



    draggingPart=null;



}









/* =====================================================
              SNAP VALIDATION
===================================================== */


function checkSnap(part){



    let type =
    part.userData.type;



    let target =
    getAssemblyPosition(

        type

    );



    if(!target)
    return;





    let distance =
    part.position.distanceTo(

        target

    );





    if(distance < 25)

    {



        animateSnap(

            part,

            target

        );



        part.userData.installed=true;



        console.log(

            "Installed",

            part.userData.name

        );



        updateStatus(

            "PART INSTALLED",

            part.userData.name

        );



    }

}









/* =====================================================
            ASSEMBLY POSITIONS
===================================================== */


function getAssemblyPosition(type){



    const positions = {


        frame:
        new THREE.Vector3(
            0,
            10,
            0
        ),



        motor:
        new THREE.Vector3(
            40,
            10,
            40
        ),



        fc:
        new THREE.Vector3(
            0,
            20,
            0
        ),



        esc:
        new THREE.Vector3(
            0,
            25,
            0
        ),



        vtx:
        new THREE.Vector3(
            -30,
            20,
            0
        ),



        rx:
        new THREE.Vector3(
            30,
            20,
            0
        ),



        gps:
        new THREE.Vector3(
            0,
            35,
            -20
        )

    };



    return positions[type];



}









/* =====================================================
              SNAP ANIMATION
===================================================== */


function animateSnap(

object,

target

){



    let start =
    object.position.clone();



    let t=0;



    function animate(){



        t+=0.08;



        object.position.lerpVectors(

            start,

            target,

            t

        );



        if(t<1)

        {

            requestAnimationFrame(
                animate
            );

        }

        else

        {

            createSnapEffect(
                object
            );

        }



    }



    animate();



}








function createSnapEffect(object){



    object.scale.set(

        1.15,

        1.15,

        1.15

    );



    setTimeout(()=>{


        object.scale.set(

            1,

            1,

            1

        );


    },150);



}








/* =====================================================
              UPDATE MOUSE
===================================================== */


function updateMouse(event){



    let rect =
    renderer.domElement
    .getBoundingClientRect();



    mouse.x =
    (
        (
        event.clientX -
        rect.left
        )
        /
        rect.width

    ) * 2 -1;




    mouse.y =
    -(
        (
        event.clientY -
        rect.top
        )
        /
        rect.height

    ) * 2 +1;



}





window.initSnapSystem =
initSnapSystem;
