let LogIn = document.getElementById("LogIn");
let Register = document.getElementById("Register");
let formIn = document.getElementById("formIn");
function openReg() {
    Register.classList.toggle("OpenReg")
    LogIn.classList.toggle("CloseLog")
    formIn.classList.toggle("pluseHight")
}