/**
 * KnowledgeHive - Settings Page
 *
 * Displays system configuration, service health, and environment information.
 */
import { useEffect, useState } from "react";
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Icon,
  Flex,
  Badge,
  Grid,
  GridItem,
  Spinner,
  Divider,
} from "@chakra-ui/react";
import {
  FiSettings,
  FiServer,
  FiCpu,
  FiDatabase,
  FiGitBranch,
  FiCheck,
  FiX,
  FiActivity,
  FiGlobe,
  FiBox,
  FiZap,
} from "react-icons/fi";
import { motion } from "framer-motion";
import { getHealth } from "../services/api";

const MotionBox = motion(Box);

/* ------------------------------------------------------------------ */
/*  Static config display                                              */
/* ------------------------------------------------------------------ */
const CONFIG_SECTIONS = [
  {
    title: "LLM Configuration",
    icon: FiCpu,
    color: "#8B5CF6",
    items: [
      { label: "Provider", value: "OpenRouter" },
      { label: "Model", value: "google/gemini-2.0-flash-001" },
      { label: "Base URL", value: "https://openrouter.ai/api/v1" },
    ],
  },
  {
    title: "Embedding Model",
    icon: FiBox,
    color: "#3B82F6",
    items: [
      { label: "Model", value: "all-MiniLM-L6-v2" },
      { label: "Provider", value: "Sentence Transformers" },
      { label: "Dimensions", value: "384" },
    ],
  },
  {
    title: "Application",
    icon: FiGlobe,
    color: "#10B981",
    items: [
      { label: "Version", value: "1.0.0" },
      { label: "Environment", value: "Development" },
      { label: "Frontend", value: "React + Chakra UI" },
      { label: "Backend", value: "FastAPI + Python" },
    ],
  },
];

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await getHealth();
        setHealth(data);
      } catch {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
  }, []);

  const ServiceStatusBadge = ({ status }) => {
    const isHealthy = status === "healthy";
    return (
      <Badge
        colorScheme={isHealthy ? "green" : "red"}
        variant="subtle"
        px={3}
        py={1}
        borderRadius="md"
        fontSize="xs"
      >
        <HStack spacing={1}>
          <Icon as={isHealthy ? FiCheck : FiX} boxSize={3} />
          <Text>{isHealthy ? "Connected" : "Disconnected"}</Text>
        </HStack>
      </Badge>
    );
  };

  return (
    <Box px={8} py={8} maxW="1200px" mx="auto">
      {/* Header */}
      <VStack spacing={1} mb={8} align="start">
        <Heading
          size="lg"
          bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
          bgClip="text"
        >
          Settings
        </Heading>
        <Text color="hive.textMuted" fontSize="sm">
          System configuration, service health, and environment information
        </Text>
      </VStack>

      <Grid templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap={6}>
        {/* Service Health */}
        <GridItem colSpan={{ base: 1, lg: 2 }}>
          <MotionBox
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
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
                <Text fontSize="md" fontWeight="600">
                  Service Health
                </Text>
                {loading && <Spinner size="sm" color="brand.400" />}
                {health && (
                  <Badge
                    colorScheme={health.status === "healthy" ? "green" : "yellow"}
                    variant="subtle"
                    px={3}
                    borderRadius="md"
                  >
                    {health.status === "healthy" ? "All Systems Operational" : "Degraded"}
                  </Badge>
                )}
              </HStack>

              <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={4}>
                {/* Qdrant */}
                <Box
                  p={4}
                  borderRadius="lg"
                  bg="hive.surface"
                  border="1px solid"
                  borderColor="hive.border"
                >
                  <HStack spacing={3} mb={3}>
                    <Flex
                      w="36px"
                      h="36px"
                      borderRadius="lg"
                      bgGradient="linear(to-br, #3B82F6, #2563EB)"
                      align="center"
                      justify="center"
                    >
                      <Icon as={FiDatabase} color="white" boxSize={4} />
                    </Flex>
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="600" fontSize="sm">
                        Qdrant
                      </Text>
                      <Text fontSize="xs" color="hive.textMuted">
                        Vector Database
                      </Text>
                    </VStack>
                  </HStack>
                  <ServiceStatusBadge status={health?.qdrant || "unknown"} />
                  <Text fontSize="xs" color="hive.textMuted" mt={2}>
                    localhost:6333
                  </Text>
                </Box>

                {/* Neo4j */}
                <Box
                  p={4}
                  borderRadius="lg"
                  bg="hive.surface"
                  border="1px solid"
                  borderColor="hive.border"
                >
                  <HStack spacing={3} mb={3}>
                    <Flex
                      w="36px"
                      h="36px"
                      borderRadius="lg"
                      bgGradient="linear(to-br, #8B5CF6, #7C3AED)"
                      align="center"
                      justify="center"
                    >
                      <Icon as={FiGitBranch} color="white" boxSize={4} />
                    </Flex>
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="600" fontSize="sm">
                        Neo4j
                      </Text>
                      <Text fontSize="xs" color="hive.textMuted">
                        Graph Database
                      </Text>
                    </VStack>
                  </HStack>
                  <ServiceStatusBadge status={health?.neo4j || "unknown"} />
                  <Text fontSize="xs" color="hive.textMuted" mt={2}>
                    bolt://localhost:7687
                  </Text>
                </Box>

                {/* Redis */}
                <Box
                  p={4}
                  borderRadius="lg"
                  bg="hive.surface"
                  border="1px solid"
                  borderColor="hive.border"
                >
                  <HStack spacing={3} mb={3}>
                    <Flex
                      w="36px"
                      h="36px"
                      borderRadius="lg"
                      bgGradient="linear(to-br, #EF4444, #DC2626)"
                      align="center"
                      justify="center"
                    >
                      <Icon as={FiZap} color="white" boxSize={4} />
                    </Flex>
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="600" fontSize="sm">
                        Redis
                      </Text>
                      <Text fontSize="xs" color="hive.textMuted">
                        Cache & Queue
                      </Text>
                    </VStack>
                  </HStack>
                  <ServiceStatusBadge status={health?.redis || "unknown"} />
                  <Text fontSize="xs" color="hive.textMuted" mt={2}>
                    localhost:6379
                  </Text>
                </Box>
              </Grid>
            </Box>
          </MotionBox>
        </GridItem>

        {/* Configuration Sections */}
        {CONFIG_SECTIONS.map((section, i) => (
          <GridItem key={section.title}>
            <MotionBox
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1, duration: 0.4 }}
            >
              <Box
                p={6}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor="hive.border"
                h="100%"
              >
                <HStack spacing={3} mb={4}>
                  <Flex
                    w="36px"
                    h="36px"
                    borderRadius="lg"
                    bg={`${section.color}20`}
                    align="center"
                    justify="center"
                  >
                    <Icon as={section.icon} color={section.color} boxSize={4} />
                  </Flex>
                  <Text fontWeight="600" fontSize="md">
                    {section.title}
                  </Text>
                </HStack>

                <VStack
                  spacing={0}
                  align="stretch"
                  divider={<Divider borderColor="hive.border" opacity={0.3} />}
                >
                  {section.items.map((item) => (
                    <HStack
                      key={item.label}
                      justify="space-between"
                      py={3}
                    >
                      <Text fontSize="sm" color="hive.textMuted">
                        {item.label}
                      </Text>
                      <Text
                        fontSize="sm"
                        fontWeight="500"
                        color="hive.text"
                        fontFamily="mono"
                      >
                        {item.value}
                      </Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            </MotionBox>
          </GridItem>
        ))}
      </Grid>
    </Box>
  );
}
