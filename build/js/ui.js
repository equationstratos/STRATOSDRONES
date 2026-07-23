/* =====================================================
   STRATOS DRONES
   TinyHoop MK1 BUILDER
   User Interface Controller
===================================================== */


let smokeTimer;



/* =====================================================
                INIT UI
===================================================== */


function initUI(){


    console.log(
        "UI system ready"
    );



    hideSmoke();



}








/* =====================================================
              STATUS MESSAGE
===================================================== */


function showMessage(

title,

text

){



    updateStatus(

        title,

        text

    );



}









/* =====================================================
              SMOKE EFFECT
===================================================== */


function showSmoke(){



    let smoke =
    document.getElementById(
        "smoke"
    );



    if(!smoke)
    return;




    smoke.style.display =
    "block";



    smoke.style.opacity =
    "1";



    if(window.playErrorSound)

    {

        playErrorSound();

    }






    smokeTimer =
    setTimeout(()=>{


        hideSmoke();



    },5000);



}








function hideSmoke(){



    let smoke =
    document.getElementById(
        "smoke"
    );



    if(smoke)

    {


        smoke.style.display =
        "none";


    }



}









/* =====================================================
              SUCCESS EFFECT
===================================================== */


function showSuccess(){



    updateStatus(

        "✔ SUCCESS",

        "TinyHoop MK1 ready"

    );



}








/* =====================================================
              BUTTON HELPERS
===================================================== */


function setButtonState(

id,

enabled

){



    let button =
    document.getElementById(id);



    if(!button)
    return;



    button.disabled =
    !enabled;



}









/* =====================================================
              SOLDER UI
===================================================== */


function openSolderUI(){



    let panel =
    document.getElementById(

        "solderMode"

    );



    if(panel)

    panel.style.display =
    "block";



}






function closeSolderUI(){



    let panel =
    document.getElementById(

        "solderMode"

    );



    if(panel)

    panel.style.display =
    "none";



}








/* =====================================================
              TEST UI
===================================================== */


function openTestUI(){



    let panel =
    document.getElementById(

        "testPanel"

    );



    if(panel)

    panel.style.display =
    "block";


}






function closeTestUI(){



    let panel =
    document.getElementById(

        "testPanel"

    );



    if(panel)

    panel.style.display =
    "none";


}









window.initUI =
initUI;


window.showSmoke =
showSmoke;


window.hideSmoke =
hideSmoke;


window.showSuccess =
showSuccess;


window.openSolderUI =
openSolderUI;


window.closeSolderUI =
closeSolderUI;


window.openTestUI =
openTestUI;


window.closeTestUI =
closeTestUI;
