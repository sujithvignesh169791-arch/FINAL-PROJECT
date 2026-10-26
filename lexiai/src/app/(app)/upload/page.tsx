"use client";

import { motion } from "framer-motion";
import { CloudUpload, File as FileIcon, X } from "lucide-react";
import { useState } from "react";
import Link from "next/link";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<{name: string, size: string, status: string, id?: string}[]>([]);

  const uploadFile = async (file: File) => {
    const fileObj = {
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + " MB",
      status: "uploading..."
    };
    
    setFiles(prev => [...prev, fileObj]);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = getAuthToken();
      if (!token) {
        alert("Please sign in first to upload documents.");
        window.location.href = "/login";
        return;
      }

      const res = await apiFetch("/api/v1/documents/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      if (res.ok) {
        // Poll status
        const docId = data.id;
        
        const poll = setInterval(async () => {
          try {
            const pollRes = await apiFetch(`/api/v1/documents/jobs/${docId}`);
            const pollData = await pollRes.json();
            if (pollData.status === "completed" || pollData.status === "failed") {
              clearInterval(poll);
              setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: pollData.status, id: docId } : f));
            } else {
              setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: pollData.status } : f));
            }
          } catch (pollErr) {
            clearInterval(poll);
          }
        }, 1500);
      } else {
        const errorMsg = typeof data.detail === "object" ? JSON.stringify(data.detail) : (data.detail || "Upload failed");
        setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: `Error: ${errorMsg}` } : f));
      }
    } catch (err) {
      setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: "Could not connect to backend" } : f));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      Array.from(e.dataTransfer.files).forEach(uploadFile);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Upload Document</h1>
        <p className="text-white/50">Upload legal documents for analysis, comparison, or risk assessment.</p>
      </div>

      <div className="glass rounded-2xl border border-white/5 bg-white/5 p-1">
        <div 
          className={`
            border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-all duration-200
            ${isDragging ? 'border-gold bg-gold/5' : 'border-white/20 hover:border-gold/50 hover:bg-white/5'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-6">
            <CloudUpload className={`w-8 h-8 ${isDragging ? 'text-gold' : 'text-white/40'}`} />
          </div>
          
          <h3 className="text-xl font-medium text-ivory mb-2">Drag & Drop files here</h3>
          <p className="text-white/40 text-sm mb-6 max-w-md text-center">
            Supported formats: PDF, DOCX, TXT. Maximum file size: 50MB. 
            All documents are encrypted end-to-end.
          </p>
          
          <label className="cursor-pointer">
            <span className="bg-gold text-charcoal font-semibold px-6 py-3 rounded-lg hover:bg-gold/90 transition-all shadow-[0_0_15px_rgba(212,175,55,0.2)]">
              Browse Files
            </span>
            <input type="file" className="hidden" multiple onChange={(e) => {
              if (e.target.files) {
                Array.from(e.target.files).forEach(uploadFile);
              }
            }} />
          </label>
        </div>
      </div>

      {files.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <h4 className="text-sm font-medium text-white/70 uppercase tracking-wider">Selected Files</h4>
          <div className="space-y-3">
            {files.map((file, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 glass-dark">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-white/10 text-ivory">
                    <FileIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-ivory">{file.name}</p>
                    <p className="text-xs text-white/50">{file.size}</p>
                  </div>
                </div>
                <button 
                  onClick={() => removeFile(i)}
                  className="p-2 rounded-lg hover:bg-burgundy/20 text-white/50 hover:text-burgundy transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button 
              onClick={() => setFiles([])}
              className="px-6 py-2.5 rounded-lg border border-white/10 text-white/70 hover:text-ivory hover:bg-white/5 transition-all text-sm font-medium"
            >
              Cancel
            </button>
            <Link href="/dashboard">
              <button className="px-6 py-2.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-all text-sm font-semibold shadow-[0_0_15px_rgba(212,175,55,0.2)]">
                Start Analysis
              </button>
            </Link>
          </div>
        </motion.div>
      )}
    </div>
  );
}
