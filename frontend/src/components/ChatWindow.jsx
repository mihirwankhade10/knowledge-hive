/**
 * KnowledgeHive - ChatWindow Component
 *
 * Chat interface with message bubbles, sources panel, and confidence display.
 */
import { useState, useRef, useEffect } from "react";
import {
  Box,
  VStack,
  HStack,
  Input,
  IconButton,
  Text,
  Flex,
  Badge,
  Spinner,
  Collapse,
  Divider,
  Tooltip,
} from "@chakra-ui/react";
import { FiSend, FiChevronDown, FiChevronUp, FiFileText } from "react-icons/fi";
import { queryKnowledge } from "../services/api";

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    // Add user message
    setMessages((prev) => [...prev, { type: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const data = await queryKnowledge(question);
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          content: data.answer,
          sources: data.sources || [],
          confidence: data.confidence || 0,
          agentFlow: data.agent_flow || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          type: "error",
          content:
            err.response?.data?.detail || "Failed to get response. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Flex direction="column" h="calc(100vh - 140px)" maxH="800px">
      {/* Messages Area */}
      <Box
        flex="1"
        overflowY="auto"
        px={4}
        py={4}
        borderRadius="xl"
        bg="hive.surface"
        border="1px solid"
        borderColor="hive.border"
        mb={4}
      >
        {messages.length === 0 ? (
          <Flex h="100%" align="center" justify="center">
            <VStack spacing={3} color="hive.textMuted">
              <Text fontSize="4xl">🐝</Text>
              <Text fontSize="lg" fontWeight="500">
                Ask KnowledgeHive anything
              </Text>
              <Text fontSize="sm">
                Upload documents first, then ask questions about your knowledge base
              </Text>
            </VStack>
          </Flex>
        ) : (
          <VStack spacing={4} align="stretch">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {loading && (
              <HStack spacing={3} p={4}>
                <Spinner size="sm" color="brand.400" />
                <Text fontSize="sm" color="hive.textMuted">
                  Agents are working...
                </Text>
              </HStack>
            )}
            <div ref={messagesEndRef} />
          </VStack>
        )}
      </Box>

      {/* Input Area */}
      <HStack spacing={3}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
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
          icon={<FiSend />}
          onClick={handleSend}
          isLoading={loading}
          aria-label="Send message"
          size="lg"
          borderRadius="xl"
          bg="brand.500"
          color="black"
          _hover={{
            bg: "brand.400",
            transform: "translateY(-1px)",
            boxShadow: "0 4px 20px rgba(255, 179, 0, 0.3)",
          }}
          transition="all 0.2s"
        />
      </HStack>
    </Flex>
  );
}

/**
 * Individual message bubble with expandable sources
 */
function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.type === "user";
  const isError = message.type === "error";

  return (
    <Box
      alignSelf={isUser ? "flex-end" : "flex-start"}
      maxW="85%"
      w={isUser ? "auto" : "100%"}
    >
      <Box
        p={4}
        borderRadius="xl"
        bg={
          isUser
            ? "brand.500"
            : isError
            ? "rgba(248, 113, 113, 0.1)"
            : "hive.card"
        }
        color={isUser ? "black" : isError ? "red.300" : "hive.text"}
        border={isUser ? "none" : "1px solid"}
        borderColor={isError ? "red.800" : "hive.border"}
      >
        <Text
          fontSize="sm"
          lineHeight="tall"
          whiteSpace="pre-wrap"
        >
          {message.content}
        </Text>

        {/* Confidence + Sources toggle */}
        {message.sources && message.sources.length > 0 && (
          <>
            <Divider my={3} borderColor="hive.border" />
            <HStack justify="space-between">
              <HStack spacing={2}>
                <Tooltip label="Confidence score based on evidence quality">
                  <Badge
                    colorScheme={
                      message.confidence > 0.7
                        ? "green"
                        : message.confidence > 0.4
                        ? "yellow"
                        : "red"
                    }
                    variant="subtle"
                    px={2}
                    borderRadius="md"
                  >
                    {(message.confidence * 100).toFixed(0)}% confidence
                  </Badge>
                </Tooltip>
                <Badge variant="subtle" colorScheme="blue" px={2} borderRadius="md">
                  {message.sources.length} sources
                </Badge>
              </HStack>
              <IconButton
                icon={showSources ? <FiChevronUp /> : <FiChevronDown />}
                size="xs"
                variant="ghost"
                onClick={() => setShowSources(!showSources)}
                aria-label="Toggle sources"
              />
            </HStack>

            <Collapse in={showSources} animateOpacity>
              <VStack spacing={2} mt={3} align="stretch">
                {message.sources.map((source, i) => (
                  <Box
                    key={i}
                    p={3}
                    borderRadius="lg"
                    bg="hive.surface"
                    border="1px solid"
                    borderColor="hive.border"
                    fontSize="xs"
                  >
                    <HStack spacing={2} mb={1}>
                      <FiFileText size={12} />
                      <Text fontWeight="600" color="brand.300">
                        {source.document_name}
                      </Text>
                      <Badge
                        size="sm"
                        colorScheme="yellow"
                        variant="outline"
                        fontSize="10px"
                      >
                        {(source.relevance_score * 100).toFixed(0)}% relevant
                      </Badge>
                    </HStack>
                    <Text color="hive.textMuted" noOfLines={3}>
                      {source.chunk_text}
                    </Text>
                  </Box>
                ))}
              </VStack>
            </Collapse>
          </>
        )}
      </Box>
    </Box>
  );
}
