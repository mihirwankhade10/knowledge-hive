/**
 * KnowledgeHive - Root Application Component
 *
 * Sets up providers (Chakra, React Query, Router) and page routing.
 */
import { ChakraProvider, Box } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import theme from "./theme";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import AgentFlow from "./pages/AgentFlow";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Box minH="100vh" bg="hive.bg">
            <Navbar />
            {/* Main content with top padding for fixed navbar */}
            <Box pt="80px" pb={8}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/agents" element={<AgentFlow />} />
              </Routes>
            </Box>
          </Box>
        </Router>
      </QueryClientProvider>
    </ChakraProvider>
  );
}

export default App;
