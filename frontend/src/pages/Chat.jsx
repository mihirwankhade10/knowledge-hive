/**
 * KnowledgeHive - Chat Page
 *
 * Full-screen chat interface for querying the knowledge base.
 */
import { Box, VStack, Heading, Text } from "@chakra-ui/react";
import ChatWindow from "../components/ChatWindow";

export default function Chat() {
  return (
    <Box maxW="900px" mx="auto" px={6} py={8}>
      <VStack spacing={2} mb={6} align="start">
        <Heading
          size="lg"
          bgGradient="linear(to-r, brand.300, brand.500)"
          bgClip="text"
        >
          Knowledge Chat
        </Heading>
        <Text color="hive.textMuted" fontSize="sm">
          Ask questions about your uploaded documents. The agent swarm will
          retrieve, validate, and synthesize answers with citations.
        </Text>
      </VStack>

      <ChatWindow />
    </Box>
  );
}
