"use client";

import { motion } from "framer-motion";
import {
  Bot,
  Send,
  Loader2,
  FileText,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  Plus
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

interface SourceItem {
  document_id: string;
  document_name: string;
  page_number?: number | null;
  chunk_index?: number | null;
  excerpt: string;
  score?: number | null;
}

interface ChatMessageState {
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[];
}

export default function AskPage() {
  const [messages, setMessages] = useState<ChatMessageState[]>([
    {
      role: "assistant",
      content:
        "Hello! I am LEXIAI. Ask me questions about your uploaded legal documents, contracts, or court filings. I will ground my answers strictly in verified document evidence."
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("all");
  const [expandedSources, setExpandedSources] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load available documents for document-scoped search
  useEffect(() => {
    const fetchDocs = async () => {
      const token = getAuthToken();
      if (!token) return;

      try {
        const res = await apiFetch("/api/v1/documents");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setDocuments(data);
          }
        }
      } catch (err) {
        console.error("Failed to load user documents:", err);
      }
    };

    fetchDocs();
  }, []);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const token = getAuthToken();
    if (!token) {
      setError("Please sign in first to query your legal documents.");
      return;
    }

    setError(null);
    setInput("");

    // Append user message to thread
    const newMessages: ChatMessageState[] = [
      ...messages,
      { role: "user", content: trimmed }
    ];
    setMessages(newMessages);
    setLoading(true);

    try {
      const payload: {
        question: string;
        document_id?: string;
        session_id?: string;
      } = {
        question: trimmed
      };

      if (selectedDocId && selectedDocId !== "all") {
        payload.document_id = selectedDocId;
      }

      if (sessionId) {
        payload.session_id = sessionId;
      }

      const res = await apiFetch("/api/v1/chat/query", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to retrieve grounded answer.");
      }

      const data = await res.json();
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || []
        }
      ]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setError(err.message || "An error occurred while answering.");
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error: ${err.message || "Failed to process query. Please verify document status and retry."}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleSources = (index: number) => {
    setExpandedSources(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([
      {
        role: "assistant",
        content:
          "Starting a new conversation. What would you like to inquire about in your legal documents?"
      }
    ]);
    setError(null);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col max-w-4xl mx-auto">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-1">Ask LEXIAI</h1>
          <p className="text-white/50 text-sm">
            Chat with your AI legal assistant grounded strictly in verified document evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Document Scope Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/50 uppercase tracking-wider hidden sm:inline">Scope:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-charcoal/80 border border-white/10 text-ivory text-xs focus:outline-none focus:ring-1 focus:ring-gold"
            >
              <option value="all">All Uploaded Documents</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleNewChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-medium text-ivory transition-colors"
            title="Start New Chat Session"
          >
            <Plus className="w-3.5 h-3.5 text-gold" />
            New Chat
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-3 rounded-lg bg-burgundy/10 border border-burgundy/30 text-ivory text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-burgundy shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 glass rounded-2xl border border-white/5 bg-white/5 flex flex-col overflow-hidden relative">
        <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-gold/5 rounded-full blur-[100px] pointer-events-none" />

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 max-w-[85%] ${
                msg.role === "user" ? "ml-auto flex-row-reverse" : ""
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "assistant"
                    ? "bg-gold text-charcoal font-bold"
                    : "bg-navy border border-gold/30 text-gold text-xs font-bold"
                }`}
              >
                {msg.role === "assistant" ? <Bot className="w-5 h-5" /> : "YOU"}
              </div>

              <div className="space-y-2 flex-1">
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                    msg.role === "assistant"
                      ? "bg-charcoal/80 border border-white/10 text-ivory rounded-tl-sm"
                      : "bg-gold/10 border border-gold/20 text-ivory rounded-tr-sm"
                  }`}
                >
                  {msg.content}
                </div>

                {/* Grounded Evidence Sources Dropdown */}
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 text-xs">
                    <button
                      onClick={() => toggleSources(i)}
                      className="flex items-center gap-1.5 text-gold/80 hover:text-gold transition-colors font-medium py-1"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>{msg.sources.length} Verified Evidence Source{msg.sources.length > 1 ? "s" : ""}</span>
                      {expandedSources[i] ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedSources[i] && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mt-2 space-y-2 border-l-2 border-gold/40 pl-3 py-1"
                      >
                        {msg.sources.map((s, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-charcoal/60 border border-white/5 space-y-1"
                          >
                            <div className="flex items-center justify-between text-white/50 text-[11px]">
                              <span className="font-semibold text-ivory">
                                {s.document_name}
                              </span>
                              <span>
                                {s.page_number ? `Page ${s.page_number}` : "Full Document"}
                              </span>
                            </div>
                            <p className="text-white/70 italic text-[11px] leading-relaxed line-clamp-3 hover:line-clamp-none">
                              &ldquo;{s.excerpt}&rdquo;
                            </p>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4 max-w-[85%]"
            >
              <div className="w-8 h-8 rounded-full bg-gold text-charcoal flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="p-4 rounded-2xl bg-charcoal/80 border border-white/10 text-ivory rounded-tl-sm flex items-center gap-3">
                <Loader2 className="w-4 h-4 text-gold animate-spin" />
                <span className="text-sm text-white/70">
                  Searching document embeddings & formulating grounded answer...
                </span>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-white/5 bg-charcoal/50">
          <div className="relative flex items-end gap-2 bg-charcoal border border-white/10 rounded-xl p-2 focus-within:ring-1 focus-within:ring-gold/50 transition-colors text-ivory">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your legal documents... (e.g., 'What are the termination clauses?')"
              className="flex-1 bg-transparent border-none placeholder:text-white/30 focus:outline-none resize-none py-2 px-2 max-h-32 text-sm"
              rows={1}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-2.5 bg-gold text-charcoal rounded-lg hover:bg-gold/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="mt-2 text-center flex items-center justify-center gap-1.5">
            <HelpCircle className="w-3 h-3 text-white/30" />
            <span className="text-[10px] text-white/30 uppercase tracking-widest">
              Grounded AI retrieval. Answers require independent legal verification.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
