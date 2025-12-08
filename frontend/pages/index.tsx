import { useState, useEffect } from "react";
import Head from "next/head";
import FileUpload from "../components/FileUpload";
import ChatInterface from "../components/ChatInterface";
import useKnowledgeBase from "../hooks/useKnowledgeBase";

export default function Home() {

  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const knowledge = useKnowledgeBase();

  // supaya kalau file upload sukses, refetch knowledge base
  useEffect(() => {
    if (uploadResult) {
      knowledge.refresh();
    }
  }, [uploadResult]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'linear-gradient(135deg,#e3ebf6 0%,#fafbff 60%)'
    }}>
      <Head>
        <title>Financial RAG Chat</title>
        <meta name="description" content="AI-powered Q&A system for financial documents" />
        <link rel="icon" href="/favicon.png" type="image/png"/>
      </Head>
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh'
      }}>
        <div style={{
          width: '100%',
          maxWidth: 500,
          background: '#fff',
          borderRadius: 16,
          boxShadow: '0 2px 24px #bec7dc22',
          padding: '32px 22px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          {/* 1. [Title] */}
          <h2 style={{
            textAlign: 'center',
            color: '#0071b7',
            fontWeight: 600,
            letterSpacing: 0.15,
            marginBottom: 13,
            marginTop: 0
          }}>
            Financial Statement Q&A
          </h2>

          {/* 2. [Knowledge base summary/checking info] */}
          <div style={{
            minHeight: 42,
            width: '100%',
            textAlign: 'center',
            marginBottom: 12,
            color: '#1a4661',
            fontSize: 16
          }}>
            {knowledge.isLoading ? (
              <>Checking knowledge base...</>
            ) : (
              knowledge.ready ? (
                <>
                  📚 <b>Knowledge base available: ({knowledge.count} data)</b>.<br />
                  You can immediately chat or <span style={{ color: "#279fb6" }}>Add new document</span>.
                </>
              ) : (
                <>
                  <b>No knowledge base available.</b>
                  <div style={{ fontSize: 15, marginTop: 4, color: '#888' }}>
                    Upload the financial statement (PDF) before start asking the model.
                  </div>
                </>
              )
            )}
          </div>

          {/* 3,4,5. [Upload file form + upload button + status info] */}
          {/* FileUpload sudah sekaligus area drag, tombol, info */}
          <FileUpload
            onUploadComplete={setUploadResult}
            onUploadError={setUploadError}
            onProcessingDone={() => {
                                    knowledge.refresh();          // <-- trigger ulang cek status
                                    }}
          />

          {/* Jika belum ada KB, kasih animasi encouragement */}
          {!knowledge.ready && !knowledge.isLoading && (
            <div style={{
              textAlign: 'center',
              marginTop: 22,
              marginBottom: 5,
              opacity: .9,
              width: '100%',
            }}>
              <svg width="70" height="70" viewBox="0 0 40 40">
                <g>
                  <rect x="13" y="12" width="14" height="18" rx="4" fill="#0071b7" opacity="0.18" />
                  <rect x="14.5" y="14" width="11" height="15" rx="3" fill="#97d4ed" />
                  <rect x="17" y="17" width="7" height="2.5" rx="1.2" fill="#0071b7">
                    <animate attributeName="width" values="3;10;3" keyTimes="0;0.5;1" dur="1.4s" repeatCount="indefinite" />
                  </rect>
                </g>
              </svg>
              <div style=
                          {{ color: "#0071b7", fontWeight: 500, fontSize: 16 }}
              >
                Upload your financial PDF to get started!
              </div>
              <div style={{ fontSize: 13, marginTop: 4, color: '#888' }}>
                The system needs the data before you could start chatting.
              </div>
            </div>
          )}

          {/* 6,7. [Chat area + chat input] */}
          <div style={{ margin: '38px 0 4px 0', width: '100%' }}>
            <ChatInterface disabled={!knowledge.ready} />
          </div>
        </div>
        {/* Footer */}
        <div style={{
          color: '#aaa',
          margin: 24,
          alignSelf: 'center',
          fontSize: 13
        }}>
          by dylinemf <span style={{ fontSize: 17 }}>✊</span>
        </div>
      </main>
    </div>
  );
}