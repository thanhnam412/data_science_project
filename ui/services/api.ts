import { BASE_API_URL } from "@/shares/constants";
import axios from "axios";

export const createAxiosClient = (baseURLKey: keyof typeof BASE_API_URL = 'DEFAULT') => {
  const client = axios.create({
    baseURL: BASE_API_URL[baseURLKey],
    headers: {
      "Content-Type": "application/json",
    },
    withCredentials: true,
  });

  client.interceptors.response.use(
    (response) => response.data,
    (error) => {
      console.error("API Error:", error.response?.data || error.message);
    }
  );

  return client;
};

export const client = createAxiosClient();
export const py_client = createAxiosClient('MLPY');
