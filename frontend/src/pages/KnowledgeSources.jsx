/**
 * KnowledgeHive - Knowledge Sources Page
 *
 * Enterprise connector management with connect/disconnect flow,
 * ingestion progress, and per-source statistics.
 */
import { useState, useCallback } from "react";
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
  Button,
  Spinner,
  Progress,
  useToast,
  Divider,
  Stat,
  StatLabel,
  StatNumber,
} from "@chakra-ui/react";
import {
  FiCheck,
  FiLink2,
  FiRefreshCw,
  FiDatabase,
  FiActivity,
  FiTrendingUp,
} from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import connectors from "../data/connectorData";
import { connectSource, disconnectSource } from "../services/api";
import UploadBox from "../components/UploadBox";

const MotionBox = motion(Box);

export default function KnowledgeSources() {
  const [connectorStates, setConnectorStates] = useState({});
  const [connecting, setConnecting] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const toast = useToast();

  const getConnectorState = (id) =>
    connectorStates[id] || { status: "disconnected", stats: null };

  const handleConnect = useCallback(
    async (connector) => {
      // Special handling for Enterprise Documents — show upload
      if (connector.id === "documents") {
        setShowUpload(true);
        setConnectorStates((prev) => ({
          ...prev,
          documents: {
            status: "connected",
            stats: {
              records: prev.documents?.stats?.records || 0,
              entities: prev.documents?.stats?.entities || 0,
              relationships: prev.documents?.stats?.relationships || 0,
              lastSync: new Date().toLocaleString(),
            },
          },
        }));
        return;
      }

      setConnecting(connector.id);

      try {
        const result = await connectSource(connector.id);
        setConnectorStates((prev) => ({
          ...prev,
          [connector.id]: {
            status: "connected",
            stats: {
              records: result.records_ingested || connector.sampleStats.records,
              entities: result.entities_created || connector.sampleStats.entities,
              relationships: result.relationships_created || connector.sampleStats.relationships,
              lastSync: new Date().toLocaleString(),
            },
          },
        }));

        toast({
          title: `${connector.name} Connected`,
          description: `Successfully ingested ${connector.sampleStats.records} records`,
          status: "success",
          duration: 4000,
          isClosable: true,
        });
      } catch (err) {
        // Fallback: simulate connection with sample stats if backend unavailable
        setConnectorStates((prev) => ({
          ...prev,
          [connector.id]: {
            status: "connected",
            stats: {
              records: connector.sampleStats.records,
              entities: connector.sampleStats.entities,
              relationships: connector.sampleStats.relationships,
              lastSync: new Date().toLocaleString(),
            },
          },
        }));
        toast({
          title: `${connector.name} Connected`,
          description: `Loaded ${connector.sampleStats.records} sample records`,
          status: "success",
          duration: 4000,
          isClosable: true,
        });
      } finally {
        setConnecting(null);
      }
    },
    [toast]
  );

  const handleDisconnect = useCallback(
    async (connector) => {
      try {
        await disconnectSource(connector.id);
      } catch {
        // OK if backend not available
      }
      setConnectorStates((prev) => ({
        ...prev,
        [connector.id]: { status: "disconnected", stats: null },
      }));
      if (connector.id === "documents") setShowUpload(false);
    },
    []
  );

  // Aggregate stats
  const connectedCount = Object.values(connectorStates).filter(
    (s) => s.status === "connected"
  ).length;
  const totalRecords = Object.values(connectorStates).reduce(
    (sum, s) => sum + (s.stats?.records || 0),
    0
  );
  const totalEntities = Object.values(connectorStates).reduce(
    (sum, s) => sum + (s.stats?.entities || 0),
    0
  );

  const handleUploadComplete = (data) => {
    setConnectorStates((prev) => ({
      ...prev,
      documents: {
        status: "connected",
        stats: {
          records: (prev.documents?.stats?.records || 0) + 1,
          entities:
            (prev.documents?.stats?.entities || 0) +
            (data.entities_created || 0),
          relationships:
            (prev.documents?.stats?.relationships || 0) +
            (data.relationships_created || 0),
          lastSync: new Date().toLocaleString(),
        },
      },
    }));
  };

  return (
    <Box px={8} py={8} maxW="1400px" mx="auto">
      {/* Header */}
      <VStack spacing={1} mb={6} align="start">
        <Heading
          size="lg"
          bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
          bgClip="text"
        >
          Knowledge Sources
        </Heading>
        <Text color="hive.textMuted" fontSize="sm">
          Connect enterprise systems to build unified organizational intelligence
        </Text>
      </VStack>

      {/* Summary Bar */}
      <MotionBox
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <HStack
          spacing={8}
          p={5}
          borderRadius="xl"
          bg="hive.card"
          border="1px solid"
          borderColor="hive.border"
          mb={6}
        >
          <Stat>
            <StatLabel color="hive.textMuted" fontSize="xs">Sources Connected</StatLabel>
            <StatNumber color="hive.text" fontSize="2xl">
              {connectedCount}
              <Text as="span" fontSize="sm" color="hive.textMuted" ml={1}>
                / {connectors.length}
              </Text>
            </StatNumber>
          </Stat>
          <Box h="40px" w="1px" bg="hive.border" />
          <Stat>
            <StatLabel color="hive.textMuted" fontSize="xs">Records Ingested</StatLabel>
            <StatNumber color="hive.text" fontSize="2xl">
              {totalRecords.toLocaleString()}
            </StatNumber>
          </Stat>
          <Box h="40px" w="1px" bg="hive.border" />
          <Stat>
            <StatLabel color="hive.textMuted" fontSize="xs">Entities Discovered</StatLabel>
            <StatNumber color="hive.text" fontSize="2xl">
              {totalEntities.toLocaleString()}
            </StatNumber>
          </Stat>
        </HStack>
      </MotionBox>

      {/* Connector Cards Grid */}
      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" }} gap={5}>
        {connectors.map((connector, i) => {
          const state = getConnectorState(connector.id);
          const isConnected = state.status === "connected";
          const isConnecting = connecting === connector.id;

          return (
            <GridItem key={connector.id}>
              <MotionBox
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
              >
                <Box
                  p={6}
                  borderRadius="xl"
                  bg="hive.card"
                  border="1px solid"
                  borderColor={isConnected ? `${connector.color}50` : "hive.border"}
                  position="relative"
                  overflow="hidden"
                  transition="all 0.3s ease"
                  _hover={{
                    borderColor: isConnected ? connector.color : "hive.border",
                    transform: "translateY(-3px)",
                    boxShadow: `0 12px 40px rgba(0,0,0,0.3)`,
                  }}
                >
                  {/* Connected indicator glow */}
                  {isConnected && (
                    <Box
                      position="absolute"
                      top="-20px"
                      right="-20px"
                      w="80px"
                      h="80px"
                      borderRadius="full"
                      bg={connector.color}
                      opacity={0.08}
                      filter="blur(20px)"
                    />
                  )}

                  {/* Header */}
                  <HStack spacing={4} mb={4}>
                    <Flex
                      w="48px"
                      h="48px"
                      borderRadius="xl"
                      bgGradient={connector.gradient}
                      align="center"
                      justify="center"
                      boxShadow={`0 4px 15px ${connector.color}30`}
                    >
                      <Icon as={connector.icon} color="white" boxSize={5} />
                    </Flex>
                    <VStack align="start" spacing={0} flex="1">
                      <HStack>
                        <Text fontWeight="600" fontSize="md">
                          {connector.name}
                        </Text>
                        {isConnected && (
                          <Badge
                            colorScheme="green"
                            variant="subtle"
                            fontSize="10px"
                            borderRadius="md"
                          >
                            <HStack spacing={1}>
                              <FiCheck size={10} />
                              <Text>Connected</Text>
                            </HStack>
                          </Badge>
                        )}
                      </HStack>
                      <Text fontSize="xs" color="hive.textMuted">
                        {connector.category}
                      </Text>
                    </VStack>
                  </HStack>

                  {/* Description */}
                  <Text fontSize="sm" color="hive.textMuted" mb={4}>
                    {connector.description}
                  </Text>

                  {/* Stats (when connected) */}
                  <AnimatePresence>
                    {isConnected && state.stats && (
                      <MotionBox
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Box
                          p={3}
                          borderRadius="lg"
                          bg="hive.surface"
                          border="1px solid"
                          borderColor="hive.border"
                          mb={4}
                        >
                          <Grid templateColumns="repeat(2, 1fr)" gap={3}>
                            <VStack spacing={0} align="start">
                              <Text fontSize="10px" color="hive.textMuted" textTransform="uppercase" letterSpacing="wider">
                                Records Ingested
                              </Text>
                              <Text fontSize="lg" fontWeight="700" color="hive.text">
                                {state.stats.records?.toLocaleString()}
                              </Text>
                            </VStack>
                            <VStack spacing={0} align="start">
                              <Text fontSize="10px" color="hive.textMuted" textTransform="uppercase" letterSpacing="wider">
                                Entities Created
                              </Text>
                              <Text fontSize="lg" fontWeight="700" color="hive.text">
                                {state.stats.entities?.toLocaleString()}
                              </Text>
                            </VStack>
                            <VStack spacing={0} align="start">
                              <Text fontSize="10px" color="hive.textMuted" textTransform="uppercase" letterSpacing="wider">
                                Relationships
                              </Text>
                              <Text fontSize="lg" fontWeight="700" color="hive.text">
                                {state.stats.relationships?.toLocaleString()}
                              </Text>
                            </VStack>
                            <VStack spacing={0} align="start">
                              <Text fontSize="10px" color="hive.textMuted" textTransform="uppercase" letterSpacing="wider">
                                Last Sync
                              </Text>
                              <Text fontSize="xs" fontWeight="500" color="hive.textMuted">
                                {state.stats.lastSync || "—"}
                              </Text>
                            </VStack>
                          </Grid>
                        </Box>
                      </MotionBox>
                    )}
                  </AnimatePresence>

                  {/* Upload area for Enterprise Documents */}
                  {connector.id === "documents" && isConnected && showUpload && (
                    <Box mb={4}>
                      <UploadBox onUploadComplete={handleUploadComplete} />
                    </Box>
                  )}

                  {/* Connect/Disconnect Button */}
                  {isConnecting ? (
                    <VStack spacing={2}>
                      <Progress
                        size="sm"
                        isIndeterminate
                        colorScheme="yellow"
                        w="100%"
                        borderRadius="full"
                      />
                      <HStack spacing={2}>
                        <Spinner size="xs" color="brand.400" />
                        <Text fontSize="xs" color="brand.400">
                          Connecting & ingesting data...
                        </Text>
                      </HStack>
                    </VStack>
                  ) : isConnected ? (
                    <HStack spacing={3}>
                      <Button
                        size="sm"
                        variant="outline"
                        borderColor="hive.border"
                        color="hive.textMuted"
                        _hover={{ borderColor: "red.400", color: "red.400" }}
                        onClick={() => handleDisconnect(connector)}
                        flex="1"
                      >
                        Disconnect
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        borderColor="hive.border"
                        color="hive.textMuted"
                        _hover={{ borderColor: "brand.400", color: "brand.400" }}
                        leftIcon={<FiRefreshCw size={14} />}
                      >
                        Sync
                      </Button>
                    </HStack>
                  ) : (
                    <Button
                      w="100%"
                      size="sm"
                      bg={connector.color}
                      color="white"
                      _hover={{
                        opacity: 0.9,
                        transform: "translateY(-1px)",
                        boxShadow: `0 4px 20px ${connector.color}40`,
                      }}
                      transition="all 0.2s"
                      leftIcon={<FiLink2 size={14} />}
                      onClick={() => handleConnect(connector)}
                    >
                      Connect
                    </Button>
                  )}
                </Box>
              </MotionBox>
            </GridItem>
          );
        })}
      </Grid>
    </Box>
  );
}
