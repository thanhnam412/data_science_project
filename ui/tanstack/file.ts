import { useMutation } from "@tanstack/react-query";
import * as file from "@/services/file";

export const usePostFile = () => {
  return useMutation({
    mutationKey: ["post-file"],
    mutationFn: file.postFile,
  });
};
