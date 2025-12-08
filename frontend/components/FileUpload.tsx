import React, { useRef, useState } from 'react';
import styles from '../styles/FileUpload.module.css';
import { API_BASE_URL } from '../config';

interface FileUploadProps {
  onUploadComplete?: (result: any) => void;
  onUploadError?: (error: string) => void;
  onProcessingDone?: () => void;
}

// Spinner only for 'Processing...' state
const Spinner = () => (
  <span className={styles.spinner}>
    <svg viewBox="0 0 38 38">
      <circle fill="none" stroke="#38b6b8" strokeWidth="4"
        strokeDasharray="55, 150" cx="19" cy="19" r="13"
        style={{ opacity: 0.7 }} />
    </svg>
  </span>
);

export default function FileUpload({
  onUploadComplete,
  onUploadError,
  onProcessingDone,
}: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingDone, setProcessingDone] = useState(false);

  // Snack: processing progress
  const [processingCount, setProcessingCount] = useState<number>(0);            // chunk count available
  const [processingTotal, setProcessingTotal] = useState<number|null>(null);    // total target chunk
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ==== HANDLER ====
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.endsWith('.pdf')) {
      setError('File harus PDF!');
      setFile(null);
      return;
    }
    setFile(f);
    setUploadProgress(0);
    setError(null);
    setProcessingDone(false);
    setProcessingCount(0);
    setProcessingTotal(null);
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f) return;
    if (!f.name.endsWith('.pdf')) {
      setError('File harus PDF!');
      setFile(null);
      return;
    }
    setFile(f);
    setUploadProgress(0);
    setError(null);
    setProcessingDone(false);
    setProcessingCount(0);
    setProcessingTotal(null);
  };

  // Poll for PDF chunking progress
  const pollProcessingStatus = () => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/chunks`);
        const data = await res.json();
        setProcessingCount(data.total_count || 0);
        // CAUTION: field name must match backend!
        setProcessingTotal(typeof data.total_target_count === 'number' ? data.total_target_count : null);

        if ((typeof data.total_target_count === 'number') &&
            data.total_count >= data.total_target_count && data.total_target_count > 0) {
          setIsProcessing(false);
          setProcessingDone(true);
          clearInterval(interval);
          if (typeof onProcessingDone === 'function') onProcessingDone();
        } else if (!data.total_target_count && data.total_count > 0) {
          // fallback: consider done
          setIsProcessing(false);
          setProcessingDone(true);
          clearInterval(interval);
          if (typeof onProcessingDone === 'function') onProcessingDone();
        }
      } catch {}
    }, 1500);
  };

  const handleUpload = () => {
    if (!file) return;
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setIsProcessing(false);
    setProcessingDone(false);
    setProcessingCount(0);
    setProcessingTotal(null);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/upload`);
    xhr.timeout = 15 * 60 * 1000;

    xhr.upload.onprogress = (event: ProgressEvent) => {
      if (event.lengthComputable) {
        setUploadProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      setIsUploading(false);
      setUploadProgress(100);
      try {
        const resp = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          onUploadComplete && onUploadComplete(resp);
          setError(null);
          setIsProcessing(true);
          setProcessingDone(false);
          setProcessingCount(0);
          setProcessingTotal(null);
          pollProcessingStatus();
        } else {
          setError(resp.detail || 'Upload error');
          setIsProcessing(false);
          setProcessingDone(false);
        }
      } catch {
        setError('Invalid server response');
        setIsProcessing(false);
        setProcessingDone(false);
      }
    };

    xhr.onerror = () => {
      setIsUploading(false);
      setError('Upload failed');
      setIsProcessing(false);
      setProcessingDone(false);
    };

    const form = new FormData();
    form.append('file', file);
    xhr.send(form);
  };

  // ==== RENDER ====
  // Percentage processing calculated
  let processingPercent = null;
  if (processingTotal && processingTotal > 0) {
    processingPercent = Math.floor((processingCount/processingTotal) * 100);
    if (processingPercent > 100) processingPercent = 100;
  }

  return (
    <div className={styles.container}>
      {/* DRAG AND DROP AREA */}
      <div
        className={`${styles.uploadArea}${file ? ` ${styles.uploadAreaHasFile}` : ''}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        tabIndex={0}
        role="button"
        title="Klik atau drop file PDF"
      >
        {file
          ? <span>📄 <b>{file.name}</b></span>
          : <>Drag &amp; drop PDF file in here or <u>browse</u></>}
      </div>

      {/* FILE INPUT */}
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        ref={inputRef}
      />

      {/* UPLOAD BUTTON */}
      <button
        type="button"
        className={styles.uploadBtn}
        onClick={handleUpload}
        disabled={!file || isUploading || isProcessing}
      >
        {isUploading ? <><Spinner /> Uploading...</>
         : (isProcessing ? <><Spinner /> Processing PDF...</> : 'Upload PDF')}
      </button>

      {/* ERROR */}
      {error && <div className={styles.error}>{error}</div>}

      {/* UPLOAD PROGRESS BAR */}
      {isUploading && (
        <div className={styles.progressbar}>
          <div className={styles.progress} style={{ width: `${uploadProgress}%` }}>
            Upload: {uploadProgress}%
          </div>
        </div>
      )}

      {/* PDF PROCESSING PROGRESS */}
      {isProcessing && (
      <div>
        {/* numeric progress if available */}
        {processingTotal && (
          <>
            {/* TEXT CENTER ALIGNMENT */}
            <div className={styles.processingText}>
              <Spinner /> 
              <span style={{fontWeight:500, color:'#0777bc'}}>
                Processing PDF: <b>{processingCount}</b> / <b>{processingTotal}</b> 
                <span style={{marginLeft:6,color:'#3cb'}}>({processingPercent}%)</span>
              </span>
            </div>
            <div className={styles.progressbar}>
              <div
                className={styles.progress}
                style={{
                  width: `${processingPercent}%`,
                  background: '#279fb6'
                }}
              />
            </div>
          </>
        )}
        {/* fallback: label if not available */}
        {!processingTotal && (
          <div className={styles.info}>
            <Spinner /> PDF is being processed on <b>server</b>...
          </div>
        )}
      </div>
    )}

      {/* DONE */}
      {processingDone && (
        <div className={styles.success}>
          ✅ Document has been processed! Feel free to start asking questions.
        </div>
      )}
    </div>
  );
}