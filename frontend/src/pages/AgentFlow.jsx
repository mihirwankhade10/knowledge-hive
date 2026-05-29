/**
 * KnowledgeHive - Agent Flow Page
 *
 * Visual pipeline showing all agents with animated connections
 * and real-time status during query execution.
 */
import { useState } from "react";
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Input,
  IconButton,
  Flex,
  Badge,
  Divider,
  Spinner,
  Grid,
  GridItem,
  Icon,
} from "@chakra-ui/react";
import { FiSend, FiArrowRight, FiZap } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import AgentStatus from "../components/AgentStatus";
import { queryKnowledge } from "../services/api";

const MotionBox = motion(Box);

const AGENTS_PIPELINE = [
  {
    agent_name: "Retrieval Agent",
    emoji: "🔍",
    description: "Searches vectors + graph for relevant context",
    status: "idle",
  },
  {
    agent_name: "Validation Agent",
    emoji: "✅",
    description: "Scores evidence quality and confidence",
    status: "idle",
  },
  {
    agent_name: "Response Agent",
    emoji: "💬",
    description: "Generates answer with citations",
    status: "idle",
  },
];

export default function AgentFlow() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentSteps, setAgentSteps] = useState(AGENTS_PIPELINE);
  const [result, setResult] = useState(null);
  const [currentAgent, setCurrentAgent] = useState(-1);

  const handleQuery = async () => {
    const question = query.trim();
    if (!question || loading) return;

    setLoading(true);
    setResult(null);

    // Simulate running state for visualization
    const steps = AGENTS_PIPELINE.map((a) => ({ ...a, status: "idle" }));

    // Animate agents one by one
    for (let i = 0; i < steps.length; i++) {
      setCurrentAgent(i);
      steps[i].status = "running";
      setAgentSteps([...steps]);
      await new Promise((r) => setTimeout(r, 300)); // Brief visual delay
    }

    try {
      const data = await queryKnowledge(question);
      setResult(data);

      // Update with actual agent flow data
      if (data.agent_flow && data.agent_flow.length > 0) {
        setAgentSteps(data.agent_flow);
      } else {
        // Mark all as completed if no flow data
        setAgentSteps(steps.map((a) => ({ ...a, status: "completed" })));
      }
    } catch (err) {
      setAgentSteps(steps.map((a) => ({ ...a, status: "failed", error: err.message })));
    } finally {
      setLoading(false);
      setCurrentAgent(-1);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleQuery();
  };

  return (
    <Box maxW="1100px" mx="auto" px={6} py={8}>
      <VStack spacing={2} mb={8} align="start">
        <Heading
          size="lg"
          bgGradient="linear(to-r, brand.300, brand.500)"
          bgClip="text"
        >
          Agent Flow Visualization
        </Heading>
        <Text color="hive.textMuted" fontSize="sm">
          Watch the agent swarm work in real-time. Enter a query to see each
          agent process your request.
        </Text>
      </VStack>

      {/* Query Input */}
      <HStack spacing={3} mb={8}>
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter a question to visualize agent flow..."
          size="lg"
          borderRadius="xl"
          bg="hive.surface"
          borderColor="hive.border"
          _focus={{
            borderColor: "brand.500",
            boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)",
          }}
          disabled={loading}
        />
        <IconButton
          icon={<FiZap />}
          onClick={handleQuery}
          isLoading={loading}
          aria-label="Run query"
          size="lg"
          borderRadius="xl"
          bg="brand.500"
          color="black"
          _hover={{
            bg: "brand.400",
            boxShadow: "0 4px 20px rgba(255, 179, 0, 0.3)",
          }}
        />
      </HStack>

      {/* Agent Pipeline Visualization */}
      <Box
        p={6}
        borderRadius="xl"
        bg="hive.card"
        border="1px solid"
        borderColor="hive.border"
        mb={8}
      >
        <HStack spacing={2} mb={6}>
          <Text fontSize="md" fontWeight="600">
            🐝 Query Pipeline
          </Text>
          {loading && (
            <Badge colorScheme="blue" variant="subtle" borderRadius="md">
              <HStack spacing={1}>
                <Spinner size="xs" />
                <Text>Processing</Text>
              </HStack>
            </Badge>
          )}
        </HStack>

        {/* Pipeline Flow */}
        <Flex align="center" justify="center" wrap="wrap" gap={3}>
          {agentSteps.map((agent, i) => (
            <HStack key={agent.agent_name} spacing={3}>
              <Box minW="280px">
                <AgentStatus agent={agent} index={i} />
              </Box>
              {i < agentSteps.length - 1 && (
                <MotionBox
                  initial={{ opacity: 0 }}
                  animate={{
                    opacity: 1,
                    color:
                      agent.status === "completed"
                        ? "var(--chakra-colors-green-400)"
                        : "var(--chakra-colors-hive-textMuted)",
                  }}
                  transition={{ delay: i * 0.2 }}
                >
                  <FiArrowRight size={20} />
                </MotionBox>
              )}
            </HStack>
          ))}
        </Flex>
      </Box>

      {/* Result Display */}
      <AnimatePresence>
        {result && (
          <MotionBox
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Box
              p={6}
              borderRadius="xl"
              bg="hive.card"
              border="1px solid"
              borderColor="hive.border"
            >
              <HStack spacing={3} mb={4}>
                <Text fontSize="md" fontWeight="600">
                  📋 Result
                </Text>
                <Badge
                  colorScheme={
                    result.confidence > 0.7
                      ? "green"
                      : result.confidence > 0.4
                      ? "yellow"
                      : "red"
                  }
                  variant="subtle"
                  px={3}
                  borderRadius="md"
                >
                  {(result.confidence * 100).toFixed(0)}% confidence
                </Badge>
              </HStack>

              <Text
                fontSize="sm"
                color="hive.text"
                whiteSpace="pre-wrap"
                lineHeight="tall"
                mb={4}
              >
                {result.answer}
              </Text>

              {result.sources && result.sources.length > 0 && (
                <>
                  <Divider borderColor="hive.border" mb={4} />
                  <Text fontSize="sm" fontWeight="600" mb={3}>
                    Sources ({result.sources.length})
                  </Text>
                  <Grid templateColumns="repeat(2, 1fr)" gap={3}>
                    {result.sources.map((source, i) => (
                      <GridItem key={i}>
                        <Box
                          p={3}
                          borderRadius="lg"
                          bg="hive.surface"
                          border="1px solid"
                          borderColor="hive.border"
                          fontSize="xs"
                        >
                          <HStack mb={1}>
                            <Text fontWeight="600" color="brand.300">
                              📄 {source.document_name}
                            </Text>
                            <Badge
                              colorScheme="yellow"
                              variant="outline"
                              fontSize="10px"
                            >
                              {(source.relevance_score * 100).toFixed(0)}%
                            </Badge>
                          </HStack>
                          <Text color="hive.textMuted" noOfLines={3}>
                            {source.chunk_text}
                          </Text>
                        </Box>
                      </GridItem>
                    ))}
                  </Grid>
                </>
              )}
            </Box>
          </MotionBox>
        )}
      </AnimatePresence>
    </Box>
  );
}
