// from https://docs.djangoproject.com/en/2.2/ref/csrf/#ajax
export function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function snakeToPascal(str = '') {
    return str.split('_').map(word => word.slice(0, 1).toUpperCase() + word.slice(1)).join('');
}

export function objectSubset(keys, source) {
    return keys.reduce((a, e) => (a[e] = source[e], a), {});
}

export function assignOverlap(obj1, obj2) {
    return Object.assign(obj1, objectSubset(Object.keys(obj1), obj2));
}


export function debounce(func, wait = 500) {
    let timeout;
    return () => {
        let args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, wait);
    }
}

export function formatDate(date) {
  let options = {year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric'};
  return (new Date(date)).toLocaleDateString("en-US", options)
}