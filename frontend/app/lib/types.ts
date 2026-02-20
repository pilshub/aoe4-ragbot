export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  activeTools?: string[];
}

export interface Source {
  type: string;
  title: string;
  url: string | null;
}

export interface SSEChunk {
  type: "token" | "sources" | "done" | "error" | "tool_call";
  content?: string;
  sources?: Source[];
}
