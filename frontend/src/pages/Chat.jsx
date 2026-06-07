/**
 * KnowledgeHive - Enterprise Chat Page
 *
 * Full-height chat interface for querying across all connected
 * enterprise knowledge sources with enhanced answer display.
 */
import { Box, VStack, HStack, Text, Heading, Badge, Flex, Icon } from "@chakra-ui/react";
import { FiMessageSquare, FiDatabase, FiZap } from "react-icons/fi";
import ChatWindow from "../components/ChatWindow";

const SUGGESTED_QUERIES = [
  "Who approved Project Atlas?",
  "What was the final decision regarding OAuth implementation?",
  "Summarize all discussions regarding Release 3.2",
  "Show all risks identified during migration planning",
  "Which Jira ticket introduced the API Gateway requirement?",
  "Who owns the deployment process?",
];

export default function Chat() {
  return (
    <Flex direction="column" h="100vh" px={6} py={6}>
      {/* Compact Header */}
      <HStack spacing={3} mb={4} flexShrink={0}>
        <Flex
          w="40px"
          h="40px"
          borderRadius="lg"
          bgGradient="linear(to-br, #EC4899, #DB2777)"
          align="center"
          justify="center"
          boxShadow="0 4px 15px rgba(236,72,153,0.3)"
        >
          <Icon as={FiMessageSquare} color="white" boxSize={5} />
        </Flex>
        <VStack spacing={0} align="start">
          <Heading
            size="md"
            bgGradient="linear(to-r, brand.300, brand.500)"
            bgClip="text"
          >
            Knowledge Assistant
          </Heading>
          <Text color="hive.textMuted" fontSize="xs">
            Query across all connected enterprise sources — Teams, Email, Jira, SharePoint, Confluence
          </Text>
        </VStack>
        <HStack ml="auto" spacing={2}>
          <Badge colorScheme="green" variant="subtle" px={2} py={1} borderRadius="md" fontSize="10px">
            <HStack spacing={1}>
              <FiZap size={10} />
              <Text>Swarm Active</Text>
            </HStack>
          </Badge>
        </HStack>
      </HStack>

      {/* Chat Window */}
      <Box flex="1" minH={0}>
        <ChatWindow suggestedQueries={SUGGESTED_QUERIES} />
      </Box>
    </Flex>
  );
}
