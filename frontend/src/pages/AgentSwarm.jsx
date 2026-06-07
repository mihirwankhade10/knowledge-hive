/**
 * KnowledgeHive - Agent Swarm Page
 *
 * Comprehensive agent monitoring dashboard with per-agent stats,
 * live execution timeline, and swarm visualization.
 */
import { useState } from "react";
import {
  Box,
  Grid,
  GridItem,
  VStack,
  HStack,
  Text,
  Heading,
  Icon,
  Flex,
  Badge,
  Input,
  IconButton,
  Spinner,
  Divider,
  Progress,
  CircularProgress,
  CircularProgressLabel,
} from "@chakra-ui/react";
import {
  FiCpu,
  FiDownload,
  FiGitBranch,
  FiSearch,
  FiCheckCircle,
  FiMessageSquare,
  FiSend,
  FiZap,
  FiArrowRight,
  FiClock,
  FiActivity,
  FiTrendingUp,
} from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { queryKnowledge } from "../services/api";

const MotionBox = motion(Box);

/* ------------------------------------------------------------------ */
/*  Agent definitions                                                   */
/* ------------------------------------------------------------------ */
const AGENTS = [
  {
    id: "ingestion",
    name: "Ingestion Agent",
    emoji: "📄",
    icon: FiDownload,
    color: "#3B82F6",
    gradient: "linear(to-br, #3B82F6, #2563EB)",
    description: "Parses documents, chunks text, generates embeddings, and stores vectors in Qdrant",
    stats: {
      tasksCompleted: 312,
      avgProcessingTime: "1.8s",
      successRate: 99.2,
      lastExecution: "2 min ago",
    },
  },
  {
    id: "graph",
    name: "Graph Agent",
    emoji: "🕸️",
    icon: FiGitBranch,
    color: "#8B5CF6",
    gradient: "linear(to-br, #8B5CF6, #7C3AED)",
    description: "Extracts entities and relationships using LLM, builds knowledge graph in Neo4j",
    stats: {
      tasksCompleted: 298,
      avgProcessingTime: "3.2s",
      successRate: 97.8,
      lastExecution: "2 min ago",
    },
  },
  {
    id: "retrieval",
    name: "Retrieval Agent",
    emoji: "🔍",
    icon: FiSearch,
    color: "#10B981",
    gradient: "linear(to-br, #10B981, #059669)",
    description: "Searches Qdrant vectors and Neo4j graph for relevant context across all sources",
    stats: {
      tasksCompleted: 532,
      avgProcessingTime: "0.4s",
      successRate: 99.8,
      lastExecution: "5 min ago",
    },
  },
  {
    id: "validation",
    name: "Validation Agent",
    emoji: "✅",
    icon: FiCheckCircle,
    color: "#F59E0B",
    gradient: "linear(to-br, #F59E0B, #D97706)",
    description: "Scores evidence quality, ranks sources by relevance, calculates confidence",
    stats: {
      tasksCompleted: 528,
      avgProcessingTime: "1.1s",
      successRate: 98.5,
      lastExecution: "5 min ago",
    },
  },
  {
    id: "response",
    name: "Response Agent",
    emoji: "💬",
    icon: FiMessageSquare,
    color: "#EC4899",
    gradient: "linear(to-br, #EC4899, #DB2777)",
    description: "Generates comprehensive answers with citations using validated evidence",
    stats: {
      tasksCompleted: 524,
      avgProcessingTime: "2.4s",
      successRate: 97.1,
      lastExecution: "5 min ago",
    },
  },
];

/* ------------------------------------------------------------------ */
/*  Pipeline stages for live execution                                  */
/* ------------------------------------------------------------------ */
const PIPELINE_STAGES = [
  { agent: "retrieval", label: "Retrieval" },
  { agent: "validation", label: "Validation" },
  { agent: "response", label: "Response" },
];

export default function AgentSwarm() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [result, setResult] = useState(null);
  const [currentAgent, setCurrentAgent] = useState(null);

  const handleQuery = async () => {
    const question = query.trim();
    if (!question || loading) return;

    setLoading(true);
    setResult(null);
    setPipelineStatus({});

    // Animate pipeline stages
    for (let i = 0; i < PIPELINE_STAGES.length; i++) {
      const stage = PIPELINE_STAGES[i];
      setCurrentAgent(stage.agent);
      setPipelineStatus((prev) => ({
        ...prev,
        [stage.agent]: "running",
      }));
      await new Promise((r) => setTimeout(r, 400));
    }

    try {
      const data = await queryKnowledge(question);
      setResult(data);

      // Mark all stages as completed
      const completed = {};
      PIPELINE_STAGES.forEach((s) => (completed[s.agent] = "completed"));
      setPipelineStatus(completed);
    } catch (err) {
      const failed = {};
      PIPELINE_STAGES.forEach((s) => (failed[s.agent] = "failed"));
      setPipelineStatus(failed);
      setResult({ answer: "Query failed. Please try again.", confidence: 0 });
    } finally {
      setLoading(false);
      setCurrentAgent(null);
    }
  };

  return (
    <Box px={8} py={8} maxW="1400px" mx="auto">
      {/* Header */}
      <VStack spacing={1} mb={6} align="start">
        <HStack>
          <Heading
            size="lg"
            bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
            bgClip="text"
          >
            Agent Swarm
          </Heading>
          <Badge colorScheme="green" variant="subtle" px={3} py={1} borderRadius="full" fontSize="xs">
            <HStack spacing={1}>
              <Box w="6px" h="6px" borderRadius="full" bg="green.400" />
              <Text>5 Active</Text>
            </HStack>
          </Badge>
        </HStack>
        <Text color="hive.textMuted" fontSize="sm">
          Monitor AI agent performance and watch the swarm process queries in real-time
        </Text>
      </VStack>

      {/* Agent Cards Grid */}
      <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)", xl: "repeat(5, 1fr)" }} gap={4} mb={8}>
        {AGENTS.map((agent, i) => (
          <GridItem key={agent.id}>
            <MotionBox
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.5 }}
            >
              <Box
                p={5}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor={
                  currentAgent === agent.id
                    ? agent.color
                    : pipelineStatus[agent.id] === "completed"
                    ? "green.600"
                    : "hive.border"
                }
                position="relative"
                overflow="hidden"
                transition="all 0.3s ease"
                _hover={{
                  transform: "translateY(-3px)",
                  boxShadow: "0 12px 40px rgba(0,0,0,0.3)",
                  borderColor: agent.color,
                }}
              >
                {/* Status glow */}
                {currentAgent === agent.id && (
                  <Box
                    position="absolute"
                    top="-30px"
                    right="-30px"
                    w="100px"
                    h="100px"
                    borderRadius="full"
                    bg={agent.color}
                    opacity={0.1}
                    filter="blur(20px)"
                  />
                )}

                {/* Header */}
                <HStack spacing={3} mb={3}>
                  <Flex
                    w="40px"
                    h="40px"
                    borderRadius="lg"
                    bgGradient={agent.gradient}
                    align="center"
                    justify="center"
                    boxShadow={`0 4px 15px ${agent.color}30`}
                  >
                    <Icon as={agent.icon} color="white" boxSize={4} />
                  </Flex>
                  <VStack align="start" spacing={0} flex="1">
                    <Text fontWeight="600" fontSize="sm" noOfLines={1}>
                      {agent.name}
                    </Text>
                    <Badge
                      colorScheme={
                        currentAgent === agent.id
                          ? "blue"
                          : pipelineStatus[agent.id] === "completed"
                          ? "green"
                          : pipelineStatus[agent.id] === "failed"
                          ? "red"
                          : "gray"
                      }
                      variant="subtle"
                      fontSize="9px"
                      borderRadius="sm"
                    >
                      {currentAgent === agent.id
                        ? "Running"
                        : pipelineStatus[agent.id] === "completed"
                        ? "Completed"
                        : pipelineStatus[agent.id] === "failed"
                        ? "Failed"
                        : "Ready"}
                    </Badge>
                  </VStack>
                </HStack>

                {/* Description */}
                <Text fontSize="xs" color="hive.textMuted" mb={4} noOfLines={2}>
                  {agent.description}
                </Text>

                {/* Stats */}
                <VStack spacing={2} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="10px" color="hive.textMuted">Tasks</Text>
                    <Text fontSize="10px" fontWeight="600" color="hive.text">
                      {agent.stats.tasksCompleted}
                    </Text>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="10px" color="hive.textMuted">Avg Time</Text>
                    <Text fontSize="10px" fontWeight="600" color="hive.text">
                      {agent.stats.avgProcessingTime}
                    </Text>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="10px" color="hive.textMuted">Success</Text>
                    <HStack spacing={1}>
                      <Text fontSize="10px" fontWeight="600" color="green.400">
                        {agent.stats.successRate}%
                      </Text>
                    </HStack>
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="10px" color="hive.textMuted">Last Run</Text>
                    <Text fontSize="10px" fontWeight="600" color="hive.textMuted">
                      {agent.stats.lastExecution}
                    </Text>
                  </HStack>
                </VStack>
              </Box>
            </MotionBox>
          </GridItem>
        ))}
      </Grid>

      {/* Live Execution Section */}
      <Box
        p={6}
        borderRadius="xl"
        bg="hive.card"
        border="1px solid"
        borderColor="hive.border"
        mb={6}
      >
        <HStack spacing={2} mb={5}>
          <Icon as={FiZap} color="brand.400" boxSize={5} />
          <Text fontSize="md" fontWeight="600">
            Live Execution Pipeline
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

        {/* Query Input */}
        <HStack spacing={3} mb={6}>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
            placeholder="Ask a question to see the agent swarm in action..."
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

        {/* Pipeline Visualization */}
        <Flex align="center" justify="center" gap={4} flexWrap="wrap">
          {PIPELINE_STAGES.map((stage, i) => {
            const agent = AGENTS.find((a) => a.id === stage.agent);
            const status = pipelineStatus[stage.agent];
            const isActive = currentAgent === stage.agent;

            return (
              <HStack key={stage.agent} spacing={4}>
                <MotionBox
                  animate={isActive ? { scale: [1, 1.05, 1] } : {}}
                  transition={{ repeat: Infinity, duration: 1 }}
                >
                  <Box
                    px={5}
                    py={3}
                    borderRadius="xl"
                    bg={
                      isActive
                        ? `${agent.color}15`
                        : status === "completed"
                        ? "rgba(74, 222, 128, 0.08)"
                        : "hive.surface"
                    }
                    border="1px solid"
                    borderColor={
                      isActive
                        ? agent.color
                        : status === "completed"
                        ? "green.600"
                        : "hive.border"
                    }
                    transition="all 0.3s"
                  >
                    <HStack spacing={2}>
                      {isActive ? (
                        <Spinner size="sm" color={agent.color} />
                      ) : status === "completed" ? (
                        <Icon as={FiCheckCircle} color="green.400" boxSize={4} />
                      ) : (
                        <Icon as={agent.icon} color="hive.textMuted" boxSize={4} />
                      )}
                      <VStack spacing={0} align="start">
                        <Text
                          fontSize="sm"
                          fontWeight="600"
                          color={
                            isActive
                              ? agent.color
                              : status === "completed"
                              ? "green.400"
                              : "hive.textMuted"
                          }
                        >
                          {stage.label}
                        </Text>
                        <Text fontSize="10px" color="hive.textMuted">
                          {isActive
                            ? "Processing..."
                            : status === "completed"
                            ? "Complete ✓"
                            : "Waiting"}
                        </Text>
                      </VStack>
                    </HStack>
                  </Box>
                </MotionBox>

                {i < PIPELINE_STAGES.length - 1 && (
                  <Icon
                    as={FiArrowRight}
                    color={
                      status === "completed" ? "green.400" : "hive.textMuted"
                    }
                    boxSize={4}
                    transition="color 0.3s"
                  />
                )}
              </HStack>
            );
          })}
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
                {result.confidence !== undefined && (
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
                )}
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
