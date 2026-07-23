/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Engineer Workshop Environment
===================================================== */


let workshopGroup;





/* =====================================================
                INIT WORKSHOP
===================================================== */


function initWorkshop(){


    console.log(
        "Workshop initialized"
    );



    workshopGroup =
    new THREE.Group();



    workshopGroup.name =
    "ENGINEER_WORKSHOP";



    scene.add(
        workshopGroup
    );



    createSiliconeMat();


    createBuildZones();


    createPartsBins();


    createTools();



}









/* =====================================================
              SILICONE ENGINEER MAT
===================================================== */


function createSiliconeMat(){



    let geometry =
    new THREE.BoxGeometry(

        500,

        3,

        320

    );



    let material =
    new THREE.MeshStandardMaterial({

        color:
        0x202020,

        roughness:
        0.9

    });




    let mat =
    new THREE.Mesh(

        geometry,

        material

    );



    mat.position.y =
    -8;



    mat.receiveShadow=true;



    workshopGroup.add(
        mat
    );



    createMatGrid();



}









/* =====================================================
              MAT GRID
===================================================== */


function createMatGrid(){



    let grid =
    new THREE.GridHelper(

        500,

        50,

        0x00aaff,

        0x333333

    );



    grid.position.y =
    -6.4;



    workshopGroup.add(

        grid

    );



}









/* =====================================================
              BUILD AREAS
===================================================== */


function createBuildZones(){



    createZone(

        "FRAME",

        -120,

        -80,

        80,

        50

    );



    createZone(

        "ELECTRONICS",

        0,

        -80,

        100,

        50

    );



    createZone(

        "MOTORS",

        120,

        -80,

        80,

        50

    );



    createZone(

        "BATTERY",

        0,

        100,

        100,

        50

    );



}









function createZone(

name,

x,

z,

w,

h

){



    let geometry =
    new THREE.PlaneGeometry(

        w,

        h

    );



    let material =
    new THREE.MeshBasicMaterial({

        color:
        0x005577,

        transparent:true,

        opacity:
        0.25

    });



    let zone =
    new THREE.Mesh(

        geometry,

        material

    );



    zone.rotation.x =
    -Math.PI/2;



    zone.position.set(

        x,

        -6,

        z

    );



    zone.userData.name =
    name;



    workshopGroup.add(
        zone
    );



}









/* =====================================================
                PARTS BOXES
===================================================== */


function createPartsBins(){



    createBin(

        "FRAME BIN",

        -170,

        60

    );



    createBin(

        "ELECTRONIC BIN",

        0,

        60

    );



    createBin(

        "HARDWARE BIN",

        170,

        60

    );



}








function createBin(

name,

x,

z

){



    let geometry =
    new THREE.BoxGeometry(

        70,

        20,

        40

    );



    let material =
    new THREE.MeshStandardMaterial({

        color:
        0x303030

    });



    let bin =
    new THREE.Mesh(

        geometry,

        material

    );



    bin.position.set(

        x,

        5,

        z

    );



    bin.userData.name =
    name;



    workshopGroup.add(
        bin
    );



}









/* =====================================================
                 TOOLS
===================================================== */


function createTools(){



    createTool(

        "SOLDER IRON",

        -180,

        -130

    );



    createTool(

        "SCREW DRIVER",

        0,

        -130

    );



    createTool(

        "CUTTER",

        180,

        -130

    );



}








function createTool(

name,

x,

z

){



    let geometry =
    new THREE.CylinderGeometry(

        3,

        3,

        50,

        16

    );



    let material =
    new THREE.MeshStandardMaterial({

        color:
        0x777777

    });



    let tool =
    new THREE.Mesh(

        geometry,

        material

    );



    tool.rotation.z =
    Math.PI/2;



    tool.position.set(

        x,

        8,

        z

    );



    tool.userData.name =
    name;



    workshopGroup.add(
        tool
    );



}









/* =====================================================
                EXPORT
===================================================== */


window.initWorkshop =
initWorkshop;
