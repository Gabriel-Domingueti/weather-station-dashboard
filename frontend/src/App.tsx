import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "@/ui/pages/Dashboard";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
