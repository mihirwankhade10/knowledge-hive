/**
 * KnowledgeHive - AgentStatus Component
 *
 * Individual agent status card showing name, status, and duration.
 */
import { Box, HStack, VStack, Text, Badge, Spinner, Icon } from "@chakra-ui/react";
import { FiCheckCircle, FiXCircle, FiClock, FiPlay } from "react-icons/fi";
import { motion } from "framer-motion";

const MotionBox = motion(Box);

const statusConfig = {
  idle: {
    color: "gray",
    icon: FiClock,
    label: "Idle",
    glow: "none",
  },
  running: {
    color: "blue",
    icon: null, // Use spinner
    label: "Running",
    glow: "0 0 20px rgba(96, 165, 250, 0.3)",
  },
  completed: {
    color: "green",
    icon: FiCheckCircle,
    label: "Completed",
    glow: "0 0 20px rgba(74, 222, 128, 0.2)",
  },
  failed: {
    color: "red",
    icon: FiXCircle,
    label: "Failed",
    glow: "0 0 20px rgba(248, 113, 113, 0.2)",
  },
};

export default function AgentStatus({ agent, index = 0 }) {
  const config = statusConfig[agent.status] || statusConfig.idle;
  const isRunning = agent.status === "running";

  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
    >
      <Box
        p={4}
        borderRadius="xl"
        bg="hive.card"
        border="1px solid"
        borderColor={
          isRunning ? `${config.color}.500` : "hive.border"
        }
        boxShadow={config.glow}
        transition="all 0.3s ease"
        _hover={{
          borderColor: `${config.color}.400`,
          transform: "translateY(-2px)",
          boxShadow: `0 8px 30px rgba(0,0,0,0.3)`,
        }}
      >
        <HStack justify="space-between" mb={2}>
          <HStack spacing={2}>
            {isRunning ? (
              <Spinner size="sm" color={`${config.color}.400`} />
            ) : (
              config.icon && (
                <Icon
                  as={config.icon}
                  color={`${config.color}.400`}
                  boxSize={4}
                />
              )
            )}
            <Text fontWeight="600" fontSize="sm">
              {agent.agent_name}
            </Text>
          </HStack>
          <Badge
            colorScheme={config.color}
            variant="subtle"
            fontSize="xs"
            borderRadius="md"
          >
            {config.label}
          </Badge>
        </HStack>

        {agent.output_summary && (
          <Text fontSize="xs" color="hive.textMuted" noOfLines={2} mb={2}>
            {agent.output_summary}
          </Text>
        )}

        {agent.duration_ms > 0 && (
          <HStack spacing={1} fontSize="xs" color="hive.textMuted">
            <FiClock size={10} />
            <Text>{(agent.duration_ms / 1000).toFixed(2)}s</Text>
          </HStack>
        )}

        {agent.error && (
          <Text fontSize="xs" color="red.300" mt={1} noOfLines={2}>
            ⚠️ {agent.error}
          </Text>
        )}
      </Box>
    </MotionBox>
  );
}
