/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   SCENE ENGINE SIMPLE
===================================================== */


var scene;
var camera;
var renderer;
var controls;
var droneRoot;



function initScene(){


    console.log(
        "Creating 3D scene"
    );



    scene = new THREE.Scene();


    scene.background =
    new THREE.Color(
        0x111111
    );



    camera =
    new THREE.PerspectiveCamera(

        45,

        window.innerWidth /
        window.innerHeight,

        0.1,

        2000

    );



    camera.position.set(

        0,

        100,

        260

    );




    var canvas =
    document.getElementById(
        "droneCanvas"
    );



    renderer =
    new THREE.WebGLRenderer({

        canvas:canvas,

        antialias:true

    });



    renderer.setSize(

        window.innerWidth,

        window.innerHeight

    );



    renderer.setPixelRatio(

        window.devicePixelRatio

    );



    renderer.shadowMap.enabled=true;





    /*
       PAS D'ORBIT CONTROLS POUR L'INSTANT
       CAMERA FIXE POUR VALIDATION
    */



    createLights();



    droneRoot =
    new THREE.Group();



    droneRoot.name =
    "TinyHoop_MK1";



    scene.add(

        droneRoot

    );



    createFloor();



    animate();



    window.addEventListener(

        "resize",

        resizeScene

    );



}









function createLights(){


    var ambient =
    new THREE.AmbientLight(

        0xffffff,

        1.5

    );


    scene.add(
        ambient
    );




    var light =
    new THREE.DirectionalLight(

        0xffffff,

        2

    );


    light.position.set(

        200,

        400,

        200

    );


    scene.add(

        light

    );


}









function createFloor(){


    var geometry =
    new THREE.PlaneGeometry(

        1000,

        1000

    );



    var material =
    new THREE.MeshStandardMaterial({

        color:0x181818

    });



    var floor =
    new THREE.Mesh(

        geometry,

        material

    );



    floor.rotation.x =
    -Math.PI/2;



    floor.position.y =
    -10;



    scene.add(

        floor

    );


}









function animate(){


    requestAnimationFrame(

        animate

    );



    renderer.render(

        scene,

        camera

    );


}









function resizeScene(){


    camera.aspect =

    window.innerWidth /
    window.innerHeight;



    camera.updateProjectionMatrix();



    renderer.setSize(

        window.innerWidth,

        window.innerHeight

    );


}







function loadDroneModel(){


    console.log(

        "GLB loading disabled"

    );


}







window.initScene =
initScene;


window.loadDroneModel =
loadDroneModel;
