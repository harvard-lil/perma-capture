/**
 * Don't let the login form submit. Instead, just trigger the formdata event,
 * to facilitate easy inspection of the form data in JS.
 */
document.addEventListener("DOMContentLoaded", () => {
  const formElem = document.querySelector('form');
  formElem.addEventListener('submit', (e) => {
    e.preventDefault();
    new FormData(formElem);
  });
});

/**
 * Spoof login logic:if the value of the form's password field ends in 'succeed',
 * show the success message. Otherwise, show the failure message.
 *
 * Usage: call inline from the login form's onformdata handler, passing in the
 * event and the name of the form's password input.
 * e.g. <form onformdata="login(event, 'pwd')"`
 */
function login(e, passwordInputName){
  const login = document.querySelector('#login');
  const success = document.querySelector('#success');
  const error = document.querySelector('#error');

  let data = e.formData;
  let displayElem = error;
  if (data.get(passwordInputName).endsWith('succeed')){
    displayElem = success;
  }
  login.style.display = 'none';
  displayElem.style.display = 'block';
}
