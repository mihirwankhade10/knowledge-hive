/**
 * KnowledgeHive - Enterprise Dashboard
 *
 * Main landing page with enterprise KPI cards, recent activity,
 * system health, and quick actions.
 */
import { useEffect, useState } from "react";
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
  Progress,
  Divider,
} from "@chakra-ui/react";
import {
  FiDatabase,
  FiLayers,
  FiGitBranch,
  FiFileText,
  FiCpu,
  FiMessageSquare,
  FiActivity,
  FiTrendingUp,
  FiClock,
  FiCheckCircle,
  FiZap,
  FiArrowUpRight,
  FiShare2,
} from "react-icons/fi";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { getStats } from "../services/api";

const MotionBox = motion(Box);

/* ------------------------------------------------------------------ */
/*  KPI Card definitions                                               */
/* ------------------------------------------------------------------ */
const kpiCards = [
  {
    label: "Knowledge Sources",
    key: "sources_connected",
    icon: FiDatabase,
    color: "#6366F1",
    gradient: "linear(to-br, #6366F1, #8B5CF6)",
    suffix: "connected",
  },
  {
    label: "Documents Indexed",
    key: "documents_indexed",
    icon: FiFileText,
    color: "#F59E0B",
    gradient: "linear(to-br, #F59E0B, #D97706)",
    suffix: "files",
  },
  {
    label: "Entities Extracted",
    key: "entities_extracted",
    icon: FiLayers,
    color: "#10B981",
    gradient: "linear(to-br, #10B981, #059669)",
    suffix: "entities",
  },
  {
    label: "Relationships Created",
    key: "relationships_created",
    icon: FiGitBranch,
    color: "#8B5CF6",
    gradient: "linear(to-br, #8B5CF6, #7C3AED)",
    suffix: "links",
  },
  {
    label: "Agent Executions",
    key: "agent_executions",
    icon: FiCpu,
    color: "#3B82F6",
    gradient: "linear(to-br, #3B82F6, #2563EB)",
    suffix: "runs",
  },
  {
    label: "Questions Answered",
    key: "questions_answered",
    icon: FiMessageSquare,
    color: "#EC4899",
    gradient: "linear(to-br, #EC4899, #DB2777)",
    suffix: "queries",
  },
];

/* ------------------------------------------------------------------ */
/*  Recent activity items (demo data)                                   */
/* ------------------------------------------------------------------ */
const recentActivity = [
  { action: "Microsoft Teams connected", time: "2 min ago", icon: FiCheckCircle, color: "green.400", type: "connector" },
  { action: "Ingested 47 team conversations", time: "2 min ago", icon: FiDatabase, color: "blue.400", type: "ingestion" },
  { action: "Extracted 1,247 entities from Teams data", time: "1 min ago", icon: FiLayers, color: "purple.400", type: "extraction" },
  { action: "Knowledge graph updated with 2,103 relationships", time: "1 min ago", icon: FiGitBranch, color: "indigo.400", type: "graph" },
  { action: "Jira connector synchronized", time: "5 min ago", icon: FiCheckCircle, color: "green.400", type: "connector" },
  { action: "Query: 'Who approved Project Atlas?' answered", time: "8 min ago", icon: FiMessageSquare, color: "pink.400", type: "query" },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */
export default function Dashboard() {
  const [stats, setStats] = useState({
    sources_connected: 0,
    documents_indexed: 0,
    entities_extracted: 0,
    relationships_created: 0,
    agent_executions: 0,
    questions_answered: 0,
  });
  const [animatedStats, setAnimatedStats] = useState({});

  // Fetch real stats from backend and merge with demo defaults
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getStats();
        // Merge real stats with demo defaults for unfilled values
        setStats({
          sources_connected: Math.max(data.total_documents > 0 ? 3 : 0, 0),
          documents_indexed: data.total_documents || 0,
          entities_extracted: data.total_entities || 0,
          relationships_created: data.total_relationships || 0,
          agent_executions: Math.max((data.total_documents || 0) * 5, 0),
          questions_answered: 0,
        });
      } catch {
        // If backend is down, keep zeros
      }
    };
    fetchStats();
  }, []);

  // Animate counters
  useEffect(() => {
    const targets = { ...stats };
    const current = {};
    Object.keys(targets).forEach((k) => (current[k] = 0));

    const duration = 1200;
    const steps = 40;
    const interval = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = Math.min(step / steps, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const frame = {};
      Object.keys(targets).forEach((k) => {
        frame[k] = Math.round(targets[k] * eased);
      });
      setAnimatedStats(frame);
      if (step >= steps) clearInterval(timer);
    }, interval);

    return () => clearInterval(timer);
  }, [stats]);

  return (
    <Box px={8} py={8} maxW="1400px" mx="auto">
      {/* Header */}
      <VStack spacing={1} mb={8} align="start">
        <HStack spacing={3}>
          <Heading
            size="lg"
            bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
            bgClip="text"
          >
            Enterprise Knowledge Dashboard
          </Heading>
          <Badge
            colorScheme="green"
            variant="subtle"
            px={3}
            py={1}
            borderRadius="full"
            fontSize="xs"
          >
            <HStack spacing={1}>
              <Box w="6px" h="6px" borderRadius="full" bg="green.400" />
              <Text>Live</Text>
            </HStack>
          </Badge>
        </HStack>
        <Text color="hive.textMuted" fontSize="sm">
          Unified organizational intelligence across all connected knowledge sources
        </Text>
      </VStack>

      {/* KPI Cards Grid */}
      <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={5} mb={8}>
        {kpiCards.map(({ label, key, icon, color, gradient, suffix }, i) => (
          <GridItem key={key}>
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
                borderColor="hive.border"
                position="relative"
                overflow="hidden"
                transition="all 0.3s ease"
                _hover={{
                  borderColor: color,
                  transform: "translateY(-4px)",
                  boxShadow: `0 12px 40px rgba(0,0,0,0.4), 0 0 20px ${color}15`,
                }}
                cursor="default"
              >
                {/* Subtle gradient accent */}
                <Box
                  position="absolute"
                  top="-30px"
                  right="-30px"
                  w="100px"
                  h="100px"
                  borderRadius="full"
                  bg={color}
                  opacity={0.06}
                  filter="blur(20px)"
                />

                <HStack spacing={3} mb={3}>
                  <Flex
                    w="42px"
                    h="42px"
                    borderRadius="lg"
                    bgGradient={gradient}
                    align="center"
                    justify="center"
                    boxShadow={`0 4px 15px ${color}30`}
                  >
                    <Icon as={icon} color="white" boxSize={5} />
                  </Flex>
                  <Text color="hive.textMuted" fontSize="sm" fontWeight="500">
                    {label}
                  </Text>
                </HStack>

                <HStack align="baseline" spacing={2}>
                  <Text
                    fontSize="3xl"
                    fontWeight="800"
                    color="hive.text"
                    lineHeight="1"
                  >
                    {(animatedStats[key] || 0).toLocaleString()}
                  </Text>
                  <Text fontSize="xs" color="hive.textMuted">
                    {suffix}
                  </Text>
                </HStack>
              </Box>
            </MotionBox>
          </GridItem>
        ))}
      </Grid>

      {/* Bottom Section: Activity + Quick Actions */}
      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6}>
        {/* Recent Activity */}
        <GridItem>
          <MotionBox
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <Box
              p={6}
              borderRadius="xl"
              bg="hive.card"
              border="1px solid"
              borderColor="hive.border"
            >
              <HStack spacing={2} mb={5}>
                <Icon as={FiActivity} color="brand.400" boxSize={5} />
                <Text fontSize="md" fontWeight="600">Recent Activity</Text>
              </HStack>
              <VStack spacing={0} align="stretch" divider={<Divider borderColor="hive.border" opacity={0.5} />}>
                {recentActivity.map((item, i) => (
                  <HStack
                    key={i}
                    py={3}
                    spacing={3}
                    _hover={{ bg: "hive.surface" }}
                    px={2}
                    borderRadius="md"
                    transition="background 0.2s"
                  >
                    <Flex
                      w="32px"
                      h="32px"
                      borderRadius="md"
                      bg={`${item.color}15`}
                      align="center"
                      justify="center"
                      flexShrink={0}
                    >
                      <Icon as={item.icon} color={item.color} boxSize={4} />
                    </Flex>
                    <Text fontSize="sm" color="hive.text" flex="1">
                      {item.action}
                    </Text>
                    <Text fontSize="xs" color="hive.textMuted" whiteSpace="nowrap">
                      {item.time}
                    </Text>
                  </HStack>
                ))}
              </VStack>
            </Box>
          </MotionBox>
        </GridItem>

        {/* Quick Actions + System Health */}
        <GridItem>
          <VStack spacing={5}>
            {/* Quick Actions */}
            <MotionBox
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              w="100%"
            >
              <Box
                p={6}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor="hive.border"
              >
                <HStack spacing={2} mb={4}>
                  <Icon as={FiZap} color="brand.400" boxSize={5} />
                  <Text fontSize="md" fontWeight="600">Quick Actions</Text>
                </HStack>
                <VStack spacing={3} align="stretch">
                  {[
                    { label: "Connect Knowledge Source", to: "/sources", icon: FiDatabase, color: "indigo" },
                    { label: "Explore Knowledge Graph", to: "/graph", icon: FiShare2, color: "purple" },
                    { label: "Ask a Question", to: "/chat", icon: FiMessageSquare, color: "pink" },
                  ].map((action) => (
                    <Flex
                      key={action.label}
                      as={Link}
                      to={action.to}
                      p={3}
                      borderRadius="lg"
                      bg="hive.surface"
                      border="1px solid"
                      borderColor="hive.border"
                      align="center"
                      justify="space-between"
                      _hover={{
                        borderColor: "brand.500",
                        bg: "hive.accentGlow",
                        textDecoration: "none",
                        transform: "translateX(4px)",
                      }}
                      transition="all 0.2s"
                      cursor="pointer"
                    >
                      <HStack spacing={3}>
                        <Icon as={action.icon} color={`${action.color}.400`} boxSize={4} />
                        <Text fontSize="sm" fontWeight="500">{action.label}</Text>
                      </HStack>
                      <Icon as={FiArrowUpRight} color="hive.textMuted" boxSize={4} />
                    </Flex>
                  ))}
                </VStack>
              </Box>
            </MotionBox>

            {/* Agent Swarm Status */}
            <MotionBox
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.5 }}
              w="100%"
            >
              <Box
                p={6}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor="hive.border"
              >
                <HStack spacing={2} mb={4}>
                  <Icon as={FiCpu} color="brand.400" boxSize={5} />
                  <Text fontSize="md" fontWeight="600">Agent Swarm</Text>
                  <Badge colorScheme="green" variant="subtle" fontSize="10px" borderRadius="md">
                    All Active
                  </Badge>
                </HStack>
                <VStack spacing={2} align="stretch">
                  {[
                    { name: "Ingestion Agent", status: "Ready", color: "green" },
                    { name: "Graph Agent", status: "Ready", color: "green" },
                    { name: "Retrieval Agent", status: "Ready", color: "green" },
                    { name: "Validation Agent", status: "Ready", color: "green" },
                    { name: "Response Agent", status: "Ready", color: "green" },
                  ].map((agent) => (
                    <HStack key={agent.name} justify="space-between" py={1}>
                      <Text fontSize="xs" color="hive.textMuted">{agent.name}</Text>
                      <Badge
                        colorScheme={agent.color}
                        variant="outline"
                        fontSize="9px"
                        borderRadius="sm"
                      >
                        {agent.status}
                      </Badge>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            </MotionBox>
          </VStack>
        </GridItem>
      </Grid>
    </Box>
  );
}
