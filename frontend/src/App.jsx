/**
 * KnowledgeHive - Root Application Component
 *
 * Enterprise Knowledge Intelligence Platform.
 * Sets up providers (Chakra, React Query, Router), sidebar layout, and page routing.
 */
import { ChakraProvider, Box, Flex } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import theme from "./theme";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import KnowledgeSources from "./pages/KnowledgeSources";
import KnowledgeGraph from "./pages/KnowledgeGraph";
import AgentSwarm from "./pages/AgentSwarm";
import Chat from "./pages/Chat";
import Settings from "./pages/Settings";

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
          <Flex minH="100vh" bg="hive.bg">
            <Sidebar />
            {/* Main content area — offset by sidebar width */}
            <Box
              flex="1"
              ml={{ base: "72px", lg: "260px" }}
              transition="margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
              minH="100vh"
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/sources" element={<KnowledgeSources />} />
                <Route path="/graph" element={<KnowledgeGraph />} />
                <Route path="/agents" element={<AgentSwarm />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Box>
          </Flex>
        </Router>
      </QueryClientProvider>
    </ChakraProvider>
  );
}

export default App;
