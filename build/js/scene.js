/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   Three.js Scene Engine
===================================================== */


let scene;
let camera;
let renderer;
let controls;

let droneRoot;

let workshopObjects = [];





/* =====================================================
                INITIALISATION SCENE
===================================================== */


function initScene(){



    const canvas =
    document.getElementById(
        "droneCanvas"
    );



    scene =
    new THREE.Scene();



    scene.background =
    new THREE.Color(
        0x101214
    );





    /*
        CAMERA
    */


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
        120,
        220

    );





    /*
        RENDERER
    */


    renderer =
    new THREE.WebGLRenderer({

        canvas:canvas,

        antialias:true

    });



    renderer.setPixelRatio(
        window.devicePixelRatio
    );



    renderer.setSize(

        window.innerWidth,

        window.innerHeight

    );



    renderer.shadowMap.enabled=true;





    /*
        CAMERA CONTROLS
    */


    controls =
    new THREE.OrbitControls(

        camera,

        renderer.domElement

    );


    controls.target.set(

        0,
        0,
        0

    );


    controls.update();





    /*
        LIGHTING
    */


    createLights();




    /*
        WORKSHOP
    */


    createEngineerMat();



    createGrid();





    /*
        EMPTY DRONE ROOT

    */


    droneRoot =
    new THREE.Group();


    droneRoot.name =
    "TinyHoop_ROOT";


    scene.add(
        droneRoot
    );





    window.addEventListener(

        "resize",

        resizeScene

    );





    animate();



}








/* =====================================================
                 LIGHTS
===================================================== */


function createLights(){



    const ambient =
    new THREE.AmbientLight(

        0xffffff,

        0.6

    );


    scene.add(
        ambient
    );




    const mainLight =
    new THREE.DirectionalLight(

        0xffffff,

        1

    );


    mainLight.position.set(

        80,
        150,
        100

    );



    mainLight.castShadow=true;


    scene.add(
        mainLight
    );





    const fill =
    new THREE.PointLight(

        0x00aaff,

        0.5,

        300

    );


    fill.position.set(

        -80,
        80,
        -100

    );


    scene.add(fill);



}







/* =====================================================
              ENGINEER BUILD MAT
===================================================== */


function createEngineerMat(){



    const geometry =
    new THREE.PlaneGeometry(

        600,

        400

    );



    const material =
    new THREE.MeshStandardMaterial({

        color:
        0x202020,

        roughness:
        0.8

    });



    const mat =
    new THREE.Mesh(

        geometry,

        material

    );



    mat.rotation.x =
    -Math.PI/2;



    mat.position.y =
    -5;



    mat.receiveShadow=true;



    scene.add(mat);



    workshopObjects.push(mat);



}








/* =====================================================
                  GRID
===================================================== */


function createGrid(){



    const grid =
    new THREE.GridHelper(

        600,

        60,

        0x555555,

        0x222222

    );



    grid.position.y =
    -4.9;



    scene.add(grid);



}









/* =====================================================
             LOAD DRONE MODEL
===================================================== */


function loadDroneModel(){



    if(!THREE.GLTFLoader)
    {

        console.warn(
            "GLTF Loader missing"
        );

        return;

    }




    const loader =
    new THREE.GLTFLoader();



    loader.load(

        STRATOS_CONFIG.modelPath,


        function(gltf){



            droneRoot.add(

                gltf.scene

            );



            gltf.scene.scale.set(

                1,
                1,
                1

            );



            console.log(

            "Drone model loaded"

            );


        },



        undefined,



        function(error){


            console.warn(

            "Model not found yet",

            error

            );


        }



    );



}









/* =====================================================
               WINDOW RESIZE
===================================================== */


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







/* =====================================================
                RENDER LOOP
===================================================== */


function animate(){


    requestAnimationFrame(
        animate
    );



    renderer.render(

        scene,

        camera

    );


}





window.initScene =
initScene;


window.loadDroneModel =
loadDroneModel;
