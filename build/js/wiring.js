/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Electronic Wiring System
===================================================== */


let wires = [];

let selectedPad = null;

let solderConnections = [];

let wireGroup;







/* =====================================================
                 INIT WIRING
===================================================== */


function initWiring(){


    console.log(
        "Wiring system initialized"
    );



    wireGroup =
    new THREE.Group();



    wireGroup.name =
    "SOLDER_WIRES";



    scene.add(
        wireGroup
    );



    createVirtualPads();


}







/* =====================================================
              CREATE SOLDER PADS
===================================================== */


let virtualPads=[];



function createVirtualPads(){



    if(!STRATOS_CONFIG.solderPoints)
    return;




    Object.keys(

        STRATOS_CONFIG.solderPoints

    )
    .forEach(

    key=>{


        let padData =
        STRATOS_CONFIG
        .solderPoints[key];



        let geometry =
        new THREE.CylinderGeometry(

            3,

            3,

            1,

            16

        );



        let material =
        new THREE.MeshStandardMaterial({

            color:
            0xffaa00,

            metalness:
            .5

        });




        let pad =
        new THREE.Mesh(

            geometry,

            material

        );



        pad.rotation.x =
        Math.PI/2;



        pad.position.set(

            padData.position.x,

            12,

            padData.position.y

        );



        pad.userData={


            id:key,


            component:
            padData.component,


            pad:
            padData.pad


        };



        scene.add(pad);



        virtualPads.push(
            pad
        );



    });


}









/* =====================================================
              PAD SELECTION
===================================================== */


function selectPad(pad){



    if(!selectedPad)

    {


        selectedPad =
        pad;



        highlightPad(
            pad,
            true
        );



        updateStatus(

            "SOLDER",

            "Select destination pad"

        );



    }

    else

    {


        createWire(

            selectedPad,

            pad

        );



        highlightPad(

            selectedPad,

            false

        );



        selectedPad=null;


    }



}








/* =====================================================
              CREATE WIRE
===================================================== */


function createWire(

startPad,

endPad

){



    console.log(

        "Wire:",

        startPad.userData.id,

        "->",

        endPad.userData.id

    );




    let start =
    startPad.position.clone();



    let end =
    endPad.position.clone();



    let distance =
    start.distanceTo(end);




    let geometry =
    new THREE.CylinderGeometry(

        .8,

        .8,

        distance,

        8

    );



    let material =
    new THREE.MeshStandardMaterial({

        color:
        0xaa0000

    });




    let cable =
    new THREE.Mesh(

        geometry,

        material

    );





    cable.position.copy(

        start.clone()
        .add(end)
        .multiplyScalar(.5)

    );





    cable.lookAt(

        end

    );





    cable.rotateX(

        Math.PI/2

    );





    wireGroup.add(

        cable

    );




    wires.push({

        mesh:cable,

        from:
        startPad.userData.id,


        to:
        endPad.userData.id


    });



    solderConnections.push({

        from:
        startPad.userData.id,


        to:
        endPad.userData.id


    });



    checkConnection(

        startPad,

        endPad

    );



}








/* =====================================================
             CONNECTION CHECK
===================================================== */


function checkConnection(

start,

end

){



    let good=false;



    STRATOS_CONFIG.wires.forEach(

    wire=>{


        if(

        (
        wire.from ===
        start.userData.id
        &&
        wire.to ===
        end.userData.id
        )

        ||

        (
        wire.from ===
        end.userData.id
        &&
        wire.to ===
        start.userData.id
        )

        )

        {


            good=true;


        }



    });





    if(good)

    {


        updateStatus(

            "CONNECTION OK",

            start.userData.id+
            " connected"

        );



    }

    else

    {


        updateStatus(

            "ERROR",

            "Wrong solder connection"

        );



    }



}









/* =====================================================
               REMOVE ALL WIRES
===================================================== */


function clearWires(){



    wires.forEach(

    wire=>{


        wireGroup.remove(

            wire.mesh

        );


    });



    wires=[];


    solderConnections=[];



}









/* =====================================================
               PAD HIGHLIGHT
===================================================== */


function highlightPad(

pad,

active

){



    if(active)

    {


        pad.material.color.set(

            0x00ff00

        );


    }

    else

    {


        pad.material.color.set(

            0xffaa00

        );


    }


}









/* =====================================================
               ENABLE CLICK PADS
===================================================== */


function enablePadSelection(){



    renderer.domElement
    .addEventListener(

    "click",

    function(event){



        let rect =
        renderer.domElement
        .getBoundingClientRect();



        let mouse =
        new THREE.Vector2();



        mouse.x =
        (
        event.clientX -
        rect.left
        )
        /
        rect.width
        *2-1;



        mouse.y =
        -(
        (
        event.clientY -
        rect.top
        )
        /
        rect.height
        )*2+1;



        let ray =
        new THREE.Raycaster();



        ray.setFromCamera(

            mouse,

            camera

        );



        let hits =
        ray.intersectObjects(

            virtualPads

        );



        if(hits.length)

        {


            selectPad(

                hits[0].object

            );


        }




    });



}









window.initWiring =
initWiring;


window.clearWires =
clearWires;


window.enablePadSelection =
enablePadSelection;
