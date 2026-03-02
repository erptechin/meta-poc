import axios from "axios";

export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5005/v1";
export const getAuthToken = () => localStorage.getItem("token") ?? null;

export const apiAxiosWithToken = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

apiAxiosWithToken.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
