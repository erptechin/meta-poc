import axios from "axios";

// base URLs - adjust as needed or use env vars (Vite uses import.meta.env)
export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5005/v1";
export const getAuthToken = () =>
  localStorage.getItem("token") ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsImVtYWlsIjoiZGVtb0BueXgudG9kYXkiLCJ0eXBlIjoiQVJUSVNUIiwiaWF0IjoxNzcyNDM5MTYxfQ.CrrcOG56I-AICwOF6922yXqSJy3Uys-x-gKqNDQtD-0";

export const apiAxiosWithToken = axios.create({ baseURL: BASE_URL });

// attach interceptor for auth token
const attachToken = (instance) => {
    instance.interceptors.request.use((config) => {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = token;
        }
        return config;
    }, (error) => Promise.reject(error));
};

attachToken(apiAxiosWithToken);
