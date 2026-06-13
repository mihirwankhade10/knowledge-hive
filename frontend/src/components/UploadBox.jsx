/**
 * KnowledgeHive - UploadBox Component
 *
 * Drag-and-drop file upload with real-time progress tracking via WebSocket.
 *
 * Phase 3: After uploading, connects to WebSocket for live ingestion progress
 * instead of blocking on the HTTP response. Falls back to sync mode if Celery
 * is unavailable.
 */
import { useCallback, useState, useRef, useEffect } from "react";
import {
  Box,
  VStack,
  Text,
  Icon,
  Badge,
  useToast,
  HStack,
  Spinner,
  Progress,
} from "@chakra-ui/react";
import { useDropzone } from "react-dropzone";
import {
  FiUploadCloud,
  FiFile,
  FiCheckCircle,
  FiAlertCircle,
  FiDatabase,
  FiGitBranch,
  FiCpu,
} from "react-icons/fi";
import { uploadDocument, subscribeToTaskProgress } from "../services/api";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/plain": [".txt"],
};

// Step display config
const STEP_CONFIG = {
  ingestion: { label: "Parsing & Embedding", icon: FiDatabase, color: "blue" },
  ingestion_complete: { label: "Chunks Created", icon: FiDatabase, color: "blue" },
  graph: { label: "Extracting Knowledge Graph", icon: FiGitBranch, color: "purple" },
  graph_complete: { label: "Graph Built", icon: FiGitBranch, color: "purple" },
  done: { label: "Complete", icon: FiCheckCircle, color: "green" },
};

export default function UploadBox({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(null);
  const [stepMessage, setStepMessage] = useState("");
  const wsRef = useRef(null);
  const toast = useToast();

  // Ref for sync processing progress animation interval
  const syncTimerRef = useRef(null);

  // Cleanup WebSocket and sync timer on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (syncTimerRef.current) {
        clearInterval(syncTimerRef.current);
      }
    };
  }, []);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setUploading(true);
      setResult(null);
      setError(null);
      setProgress(0);
      setCurrentStep(null);
      setStepMessage("Uploading file...");

      try {
        // Upload with real HTTP progress tracking (mapped to 0–50%)
        const data = await uploadDocument(file, {
          onUploadProgress: (percent) => {
            // Map HTTP upload progress to 0–50% of the total bar
            const mapped = Math.round(percent * 0.5);
            setProgress(mapped);
            if (percent >= 100) {
              setStepMessage("File uploaded. Processing...");
            }
          },
        });

        // Phase 3: async upload — connect to WebSocket for progress
        if (data.task_id && data.status === "accepted") {
          setStepMessage("File accepted. Starting processing...");
          setProgress(50);

          const { ws } = subscribeToTaskProgress(
            data.task_id,
            // onProgress — map WS progress (0–100) to 50–100% of the bar
            (update) => {
              const wsProgress = update.progress || 0;
              const mapped = 50 + Math.round(wsProgress * 0.5);
              setProgress(mapped);
              setCurrentStep(update.step || null);
              setStepMessage(update.message || "Processing...");
            },
            // onComplete
            (completeData) => {
              setResult({
                filename: completeData.filename || file.name,
                chunks_created: completeData.chunks_created || 0,
                entities_created: completeData.entities_created || 0,
                relationships_created: completeData.relationships_created || 0,
                message: completeData.message,
                elapsed_seconds: completeData.elapsed_seconds,
              });
              setUploading(false);
              setProgress(100);
              setCurrentStep("done");
              toast({
                title: "Upload Successful",
                description: completeData.message || `${file.name} processed successfully`,
                status: "success",
                duration: 5000,
                isClosable: true,
              });
              if (onUploadComplete) onUploadComplete(completeData);
            },
            // onError
            (errData) => {
              const msg = errData.error || errData.message || "Processing failed";
              setError(msg);
              setUploading(false);
              // Don't reset progress to 0 — leave it at last value
              toast({
                title: "Processing Failed",
                description: msg,
                status: "error",
                duration: 5000,
                isClosable: true,
              });
            }
          );
          wsRef.current = ws;
        } else {
          // ── Sync mode fallback (Celery not available) ──
          // The HTTP request already completed (data is the final result).
          // Show completion immediately.
          setResult(data);
          setUploading(false);
          setProgress(100);
          setCurrentStep("done");
          toast({
            title: "Upload Successful",
            description: data.message || `${file.name} processed successfully`,
            status: "success",
            duration: 5000,
            isClosable: true,
          });
          if (onUploadComplete) onUploadComplete(data);
        }
      } catch (err) {
        const msg = err.response?.data?.message || err.response?.data?.detail || err.message || "Upload failed";
        setError(msg);
        setUploading(false);
        // Don't reset progress to 0 — leave it visible so user sees where it failed
        toast({
          title: "Upload Failed",
          description: msg,
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    },
    [toast, onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <Box w="100%">
      <Box
        {...getRootProps()}
        p={8}
        borderRadius="xl"
        border="2px dashed"
        borderColor={
          isDragActive ? "brand.400" : uploading ? "hive.border" : "hive.border"
        }
        bg={isDragActive ? "hive.accentGlow" : "hive.surface"}
        cursor={uploading ? "not-allowed" : "pointer"}
        transition="all 0.3s ease"
        _hover={
          !uploading
            ? {
                borderColor: "brand.500",
                bg: "hive.accentGlow",
                transform: "translateY(-2px)",
                boxShadow: "0 8px 30px rgba(255, 179, 0, 0.1)",
              }
            : {}
        }
      >
        <input {...getInputProps()} />
        <VStack spacing={3}>
          {uploading ? (
            <>
              {/* Live Progress Display */}
              <Spinner size="lg" color="brand.400" thickness="3px" />
              <Text color="brand.400" fontWeight="500">
                {stepMessage}
              </Text>

              {/* Step-by-step progress bar */}
              <Box w="100%" maxW="320px">
                <Progress
                  value={progress}
                  size="sm"
                  colorScheme="yellow"
                  borderRadius="full"
                  hasStripe
                  isAnimated
                />
                <Text
                  fontSize="xs"
                  color="hive.textMuted"
                  mt={1}
                  textAlign="center"
                >
                  {progress}%
                </Text>
              </Box>

              {/* Active Step Badge */}
              {currentStep && STEP_CONFIG[currentStep] && (
                <HStack spacing={2}>
                  <Icon
                    as={STEP_CONFIG[currentStep].icon}
                    color={`${STEP_CONFIG[currentStep].color}.400`}
                    boxSize={4}
                  />
                  <Badge
                    colorScheme={STEP_CONFIG[currentStep].color}
                    variant="subtle"
                    fontSize="xs"
                  >
                    {STEP_CONFIG[currentStep].label}
                  </Badge>
                </HStack>
              )}
            </>
          ) : (
            <>
              <Icon
                as={FiUploadCloud}
                boxSize={10}
                color={isDragActive ? "brand.400" : "hive.textMuted"}
                transition="all 0.2s"
              />
              <Text
                fontSize="md"
                fontWeight="500"
                color={isDragActive ? "brand.400" : "hive.text"}
              >
                {isDragActive
                  ? "Drop your file here"
                  : "Drag & drop a document, or click to browse"}
              </Text>
              <HStack spacing={2}>
                <Badge colorScheme="yellow" variant="subtle">PDF</Badge>
                <Badge colorScheme="blue" variant="subtle">DOCX</Badge>
                <Badge colorScheme="green" variant="subtle">TXT</Badge>
              </HStack>
              <Text fontSize="xs" color="hive.textMuted">
                Max file size: 50MB
              </Text>
            </>
          )}
        </VStack>
      </Box>

      {/* Result display */}
      {result && (
        <Box
          mt={4}
          p={4}
          borderRadius="lg"
          bg="rgba(74, 222, 128, 0.08)"
          border="1px solid"
          borderColor="green.800"
        >
          <HStack spacing={2} mb={2}>
            <FiCheckCircle color="var(--chakra-colors-green-400)" />
            <Text fontWeight="600" color="green.300">
              Processing Complete
            </Text>
            {result.elapsed_seconds && (
              <Badge colorScheme="green" variant="outline" fontSize="xs">
                {result.elapsed_seconds}s
              </Badge>
            )}
          </HStack>
          <VStack align="start" spacing={1} fontSize="sm" color="hive.textMuted">
            <Text>📄 {result.filename}</Text>
            <Text>📦 {result.chunks_created} chunks created</Text>
            <Text>🔗 {result.entities_created} entities extracted</Text>
            <Text>🕸️ {result.relationships_created} relationships found</Text>
          </VStack>
        </Box>
      )}

      {/* Error display */}
      {error && (
        <Box
          mt={4}
          p={4}
          borderRadius="lg"
          bg="rgba(248, 113, 113, 0.08)"
          border="1px solid"
          borderColor="red.800"
        >
          <HStack spacing={2}>
            <FiAlertCircle color="var(--chakra-colors-red-400)" />
            <Text fontWeight="600" color="red.300">
              {error}
            </Text>
          </HStack>
        </Box>
      )}
    </Box>
  );
}
