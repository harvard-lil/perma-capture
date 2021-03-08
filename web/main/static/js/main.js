//
// A11Y
//
const srAnnouncementsIntro = document.getElementById('sr-announcements-intro');
const srAnnouncements = document.getElementById('sr-announcements');

srAnnouncementsIntro.setAttribute( 'hidden', 'hidden' );

function say(text){
  srAnnouncementsIntro.removeAttribute( 'hidden' );
  srAnnouncements.innerText = text;
}

//
// New API token button
//

// from https://docs.djangoproject.com/en/3.0/ref/csrf/#ajax
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCsrfToken(){
  return getCookie('csrftoken');
}

if (!(typeof RESET_TOKEN_BUTTON === 'undefined') && RESET_TOKEN_BUTTON) {

  const apiKey = document.getElementById('api-key');
  const apiKeyButton = document.getElementById('api-key-button');

  function getNewApiToken(){
    fetch(RESET_TOKEN_URL, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Accept': 'application/json'
        },
    }).then(response => response.json())
      .then(data => {
        apiKey.value = data.token;
        say('Success: API token reset');
      })
      .catch((error) => {
        console.error('Token reset failed:', error);
        alert('There was a problem getting your token. Please try again.')
      });
  }

  apiKeyButton.addEventListener('click', function(event){
    getNewApiToken()
  });

}
