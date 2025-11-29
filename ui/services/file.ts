
import { client } from "./api";

export const postFile = async (data: any): Promise<
  any
> => {
  return client.post(`/read-file`, data);
};
