/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   PARTS MANAGER FIXED
===================================================== */


var droneParts = [];

var selectedPart = null;




function initPartsManager(){


    console.log(
        "Parts Manager initialized"
    );


    createAllParts();


}







function createAllParts(){



    createPart(
        "FRAME",
        "frame",
        -120,
        20,
        -80
    );


    createPart(
        "FLIGHT CONTROLLER",
        "fc",
        -40,
        20,
        -80
    );


    createPart(
        "ESC",
        "esc",
        40,
        20,
        -80
    );


    createPart(
        "VTX",
        "vtx",
        120,
        20,
        -80
    );



    createPart(
        "RX ELRS",
        "rx",
        -100,
        20,
        40
    );


    createPart(
        "GPS",
        "gps",
        0,
        20,
        40
    );


    createPart(
        "BUZZER",
        "buzzer",
        80,
        20,
        40
    );



    for(
        var i=0;
        i<4;
        i++
    )
    {

        createPart(

            "MOTOR "+(i+1),

            "motor",

            -120+(i*80),

            20,

            120

        );

    }



    createPart(
        "BATTERY",
        "battery",
        0,
        20,
        180
    );



}









function createPart(

name,

type,

x,

y,

z

){



    var geometry;



    if(type=="motor")
    {


        geometry =
        new THREE.CylinderGeometry(

            12,

            12,

            8,

            32

        );


    }

    else if(type=="battery")
    {


        geometry =
        new THREE.BoxGeometry(

            50,

            15,

            25

        );


    }

    else if(type=="frame")
    {


        geometry =
        new THREE.BoxGeometry(

            90,

            5,

            70

        );


    }

    else

    {


        geometry =
        new THREE.BoxGeometry(

            25,

            10,

            25

        );


    }





    var material =
    new THREE.MeshStandardMaterial({

        color:getPartColor(type),

        roughness:0.5


    });





    var mesh =
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



    console.log(

        "PART CREATED:",

        name,

        mesh.position

    );



}









function getPartColor(type){



    switch(type)

    {

        case "frame":
            return 0x222222;


        case "motor":
            return 0x888888;


        case "battery":
            return 0xff9900;


        case "fc":
            return 0x00aa00;


        case "esc":
            return 0x0066ff;


        case "vtx":
            return 0xff0000;


        case "rx":
            return 0xffffff;


        default:
            return 0x555555;

    }


}









function sortPartsOnBench(){



    console.log(
        "Sorting components..."
    );



    droneParts.forEach(

        function(part,index){


            var x =
            -150 + 
            ((index%5)*70);



            var z =
            -40 +
            (Math.floor(index/5)*70);



            part.position.set(

                x,

                20,

                z

            );


        }


    );


}









window.initPartsManager =
initPartsManager;


window.sortPartsOnBench =
sortPartsOnBench;


window.droneParts =
droneParts;
