import qs from "qs";
import AxiosConfig from "axios";
import { getCookie } from "../lib/helpers";

let headers = {"Content-Type": "application/json",
               "Accept": "application/json"};

const csrf_token = getCookie("csrftoken");
if(csrf_token) headers["X-CSRFToken"] = csrf_token;

const Axios = AxiosConfig.create({
    headers: headers,
    paramsSerializer(params) {
        return qs.stringify(params, {arrayFormat: "comma"});
    }
});

// Handle django.contrib.auth form validation errors
Axios.interceptors.response.use(response => {
    const nestedForm = response.data?.form?.form;
    if(nestedForm) response.data.form = nestedForm;
    return response.data?.form?.is_valid === false
        ? Promise.reject(response.data.form.errors)
        : response;
});

export default Axios;
