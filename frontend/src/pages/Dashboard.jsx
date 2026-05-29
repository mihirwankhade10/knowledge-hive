/**
 * KnowledgeHive - Dashboard Page
 *
 * Main landing page with file upload, knowledge stats, and overview.
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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Icon,
  Flex,
  keyframes,
} from "@chakra-ui/react";
import { FiDatabase, FiLayers, FiGitBranch, FiFileText } from "react-icons/fi";
import { motion } from "framer-motion";
import UploadBox from "../components/UploadBox";
import { getStats } from "../services/api";

const MotionBox = motion(Box);

const pulseGlow = keyframes`
  0% { box-shadow: 0 0 5px rgba(255, 179, 0, 0.1); }
  50% { box-shadow: 0 0 20px rgba(255, 179, 0, 0.2); }
  100% { box-shadow: 0 0 5px rgba(255, 179, 0, 0.1); }
`;

const statCards = [
  { label: "Documents", key: "total_documents", icon: FiFileText, color: "brand.400" },
  { label: "Chunks", key: "total_chunks", icon: FiLayers, color: "blue.400" },
  { label: "Entities", key: "total_entities", icon: FiDatabase, color: "green.400" },
  { label: "Relationships", key: "total_relationships", icon: FiGitBranch, color: "purple.400" },
];

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_documents: 0,
    total_chunks: 0,
    total_entities: 0,
    total_relationships: 0,
  });

  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      // Stats unavailable - keep defaults
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleUploadComplete = () => {
    fetchStats();
  };

  return (
    <Box maxW="1200px" mx="auto" px={6} py={8}>
      {/* Header */}
      <VStack spacing={2} mb={8} align="start">
        <Heading
          size="lg"
          bgGradient="linear(to-r, brand.300, brand.500, brand.700)"
          bgClip="text"
        >
          Knowledge Dashboard
        </Heading>
        <Text color="hive.textMuted">
          Upload documents and monitor your enterprise knowledge base
        </Text>
      </VStack>

      {/* Stats Grid */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={8}>
        {statCards.map(({ label, key, icon, color }, i) => (
          <GridItem key={key}>
            <MotionBox
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
            >
              <Box
                p={5}
                borderRadius="xl"
                bg="hive.card"
                border="1px solid"
                borderColor="hive.border"
                transition="all 0.3s ease"
                _hover={{
                  borderColor: color,
                  transform: "translateY(-3px)",
                  boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
                }}
              >
                <Stat>
                  <HStack spacing={3} mb={2}>
                    <Flex
                      w="40px"
                      h="40px"
                      borderRadius="lg"
                      bg={`${color}15`}
                      align="center"
                      justify="center"
                    >
                      <Icon as={icon} color={color} boxSize={5} />
                    </Flex>
                    <StatLabel color="hive.textMuted" fontSize="sm">
                      {label}
                    </StatLabel>
                  </HStack>
                  <StatNumber
                    fontSize="2xl"
                    fontWeight="700"
                    bgGradient={`linear(to-r, ${color}, hive.text)`}
                    bgClip="text"
                  >
                    {stats[key]?.toLocaleString() || 0}
                  </StatNumber>
                  <StatHelpText fontSize="xs" color="hive.textMuted" mb={0}>
                    in knowledge base
                  </StatHelpText>
                </Stat>
              </Box>
            </MotionBox>
          </GridItem>
        ))}
      </Grid>

      {/* Upload Section */}
      <Grid templateColumns="1fr 1fr" gap={8}>
        <GridItem>
          <Box
            p={6}
            borderRadius="xl"
            bg="hive.card"
            border="1px solid"
            borderColor="hive.border"
            animation={`${pulseGlow} 4s ease-in-out infinite`}
          >
            <HStack spacing={2} mb={4}>
              <Text fontSize="lg" fontWeight="600">
                📁 Upload Document
              </Text>
            </HStack>
            <UploadBox onUploadComplete={handleUploadComplete} />
          </Box>
        </GridItem>

        <GridItem>
          <VStack spacing={4} align="stretch">
            {/* Agent Swarm Overview */}
            <Box
              p={6}
              borderRadius="xl"
              bg="hive.card"
              border="1px solid"
              borderColor="hive.border"
            >
              <Text fontSize="lg" fontWeight="600" mb={4}>
                🐝 Agent Swarm
              </Text>
              <VStack spacing={3} align="stretch">
                {[
                  { name: "Ingestion Agent", desc: "Parse, chunk, embed documents", emoji: "📄" },
                  { name: "Graph Agent", desc: "Extract entities & relationships", emoji: "🕸️" },
                  { name: "Retrieval Agent", desc: "Semantic & graph search", emoji: "🔍" },
                  { name: "Validation Agent", desc: "Score evidence & confidence", emoji: "✅" },
                  { name: "Response Agent", desc: "Generate cited answers", emoji: "💬" },
                ].map((agent, i) => (
                  <MotionBox
                    key={agent.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + i * 0.1 }}
                  >
                    <HStack
                      p={3}
                      borderRadius="lg"
                      bg="hive.surface"
                      border="1px solid"
                      borderColor="hive.border"
                      _hover={{ borderColor: "brand.500", bg: "hive.accentGlow" }}
                      transition="all 0.2s"
                    >
                      <Text fontSize="lg">{agent.emoji}</Text>
                      <VStack align="start" spacing={0}>
                        <Text fontSize="sm" fontWeight="500">{agent.name}</Text>
                        <Text fontSize="xs" color="hive.textMuted">{agent.desc}</Text>
                      </VStack>
                    </HStack>
                  </MotionBox>
                ))}
              </VStack>
            </Box>
          </VStack>
        </GridItem>
      </Grid>
    </Box>
  );
}
