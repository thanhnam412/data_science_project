"use client";

import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { PropsWithChildren } from "react";

const queryClient = new QueryClient()

const Provider = ({ children }: PropsWithChildren) => {
  return (
      <QueryClientProvider client={queryClient}>
       {children}
      </QueryClientProvider>
  );
};


export default Provider;
