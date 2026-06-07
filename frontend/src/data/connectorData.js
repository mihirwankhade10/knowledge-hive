/**
 * KnowledgeHive - Connector Configuration Data
 *
 * Metadata for enterprise knowledge source connectors.
 * Icons use react-icons; status/stats managed by frontend state + backend.
 */
import {
  FiMessageSquare,
  FiMail,
  FiClipboard,
  FiFolder,
  FiBook,
  FiFileText,
} from "react-icons/fi";

const connectors = [
  {
    id: "teams",
    name: "Microsoft Teams",
    description: "Team conversations, discussions and collaboration history",
    icon: FiMessageSquare,
    color: "#6264A7",
    gradient: "linear(to-br, #6264A7, #4B4D8F)",
    category: "Communication",
    sampleStats: {
      records: 47,
      entities: 1247,
      relationships: 2103,
    },
  },
  {
    id: "emails",
    name: "Outlook Email",
    description: "Email communication and approvals",
    icon: FiMail,
    color: "#0078D4",
    gradient: "linear(to-br, #0078D4, #005A9E)",
    category: "Communication",
    sampleStats: {
      records: 38,
      entities: 892,
      relationships: 1456,
    },
  },
  {
    id: "jira",
    name: "Jira",
    description: "Project management and ticket history",
    icon: FiClipboard,
    color: "#0052CC",
    gradient: "linear(to-br, #0052CC, #003D99)",
    category: "Project Management",
    sampleStats: {
      records: 64,
      entities: 2341,
      relationships: 3892,
    },
  },
  {
    id: "sharepoint",
    name: "SharePoint",
    description: "Enterprise document repository",
    icon: FiFolder,
    color: "#038387",
    gradient: "linear(to-br, #038387, #025D60)",
    category: "Documents",
    sampleStats: {
      records: 23,
      entities: 1567,
      relationships: 2234,
    },
  },
  {
    id: "confluence",
    name: "Confluence",
    description: "Knowledge base and documentation",
    icon: FiBook,
    color: "#172B4D",
    gradient: "linear(to-br, #0052CC, #172B4D)",
    category: "Documentation",
    sampleStats: {
      records: 31,
      entities: 1893,
      relationships: 2987,
    },
  },
  {
    id: "documents",
    name: "Enterprise Documents",
    description: "PDF, DOCX and TXT files",
    icon: FiFileText,
    color: "#F59E0B",
    gradient: "linear(to-br, #F59E0B, #D97706)",
    category: "Documents",
    sampleStats: {
      records: 12,
      entities: 492,
      relationships: 1437,
    },
  },
];

export default connectors;
