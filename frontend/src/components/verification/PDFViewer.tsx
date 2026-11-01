import React, { useState, useMemo } from 'react';
import {
  FileText,
  ExternalLink,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle2,
  Copy,
} from 'lucide-react';
import { documentsService } from '../../services/documents.service';
import { useQuery } from '@tanstack/react-query';

interface PDFViewerProps {
  documentId?: string;
  filename?: string;
  highlightPage?: number | null;
  highlightText?: string | null;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  documentId,
  filename = 'Commercial Document',
  highlightPage,
  highlightText,
}) => {
  const [zoomLevel, setZoomLevel] = useState(100);
  const [viewMode, setViewMode] = useState<'pdf' | 'text'>('pdf');
  const [copied, setCopied] = useState(false);

  // Fetch extraction text for provenance inspector
  const { data: extraction } = useQuery({
    queryKey: ['document-extraction', documentId],
    queryFn: () => (documentId ? documentsService.getDocumentExtraction(documentId) : null),
    enabled: !!documentId,
  });

  const fileUrl = documentId ? documentsService.getDocumentFileUrl(documentId) : '';

  const pdfUrlWithParams = useMemo(() => {
    if (!fileUrl) return '';
    const params: string[] = [];
    if (highlightPage) params.push(`page=${highlightPage}`);
    if (zoomLevel !== 100) params.push(`zoom=${zoomLevel}`);
    params.push('toolbar=1');
    const hash = params.join('&');
    return hash ? `${fileUrl}#${hash}` : fileUrl;
  }, [fileUrl, highlightPage, zoomLevel]);

  if (!documentId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-200 rounded-xl text-center">
        <FileText className="w-12 h-12 text-slate-300 mb-3" />
        <p className="text-sm font-semibold text-slate-600">No Document Selected</p>
        <p className="text-xs text-slate-400 mt-1 max-w-xs">
          Select a commercial document from the left pane to view its digital PDF pages and source evidence.
        </p>
      </div>
    );
  }

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 20, 200));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 20, 60));
  const handleResetZoom = () => setZoomLevel(100);

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      {/* Viewer Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
          <span className="font-semibold text-slate-900 truncate max-w-[200px]" title={filename}>
            {filename}
          </span>
          {highlightPage && (
            <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold text-[10px]">
              Page {highlightPage}
            </span>
          )}
        </div>

        {/* View Mode Toggle: Digital PDF vs Extracted Text */}
        <div className="flex items-center bg-slate-200/80 p-0.5 rounded-lg text-xs font-semibold">
          <button
            onClick={() => setViewMode('pdf')}
            className={`px-2.5 py-1 rounded-md transition ${
              viewMode === 'pdf'
                ? 'bg-white text-blue-700 shadow-subtle'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Digital PDF
          </button>
          <button
            onClick={() => setViewMode('text')}
            className={`px-2.5 py-1 rounded-md transition ${
              viewMode === 'text'
                ? 'bg-white text-blue-700 shadow-subtle'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Extracted Text
          </button>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          {viewMode === 'pdf' && (
            <>
              <button
                onClick={handleZoomOut}
                className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[11px] font-mono text-slate-500 w-9 text-center">
                {zoomLevel}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleResetZoom}
                className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition"
                title="Reset Zoom"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <div className="h-4 w-px bg-slate-300 mx-1" />
            </>
          )}

          <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600 inline-flex items-center transition"
            title="Open in new window"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <a
            href={fileUrl}
            download={filename}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600 inline-flex items-center transition"
            title="Download PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Traceable Source Text Banner if inspecting a specific discrepancy */}
      {highlightText && (
        <div className="px-4 py-2 bg-amber-50/90 border-b border-amber-200 flex items-start justify-between gap-2 text-xs">
          <div className="flex items-start gap-2">
            <span className="font-bold text-amber-900 shrink-0 mt-0.5">Discrepancy Source Evidence:</span>
            <code className="text-amber-950 bg-amber-100/80 px-2 py-0.5 rounded font-mono text-[11px] break-all border border-amber-300/60">
              "{highlightText}"
            </code>
          </div>
          <button
            onClick={() => handleCopyText(highlightText)}
            className="text-amber-800 hover:text-amber-950 p-1 rounded hover:bg-amber-100/60 transition"
            title="Copy source evidence"
          >
            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 w-full h-full min-h-[520px] bg-slate-100 relative overflow-hidden flex flex-col">
        {viewMode === 'pdf' ? (
          <div className="w-full h-full flex-1 relative bg-white">
            <iframe
              key={`${documentId}-${highlightPage || 1}`}
              src={pdfUrlWithParams}
              title={filename}
              className="w-full h-full min-h-[550px] border-none bg-white rounded-b-xl"
            />
          </div>
        ) : (
          <div className="p-4 h-full overflow-y-auto space-y-4 bg-white text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">
                Extracted Document Pages ({extraction?.pages?.length || 1})
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                Method: {extraction?.extraction_method || 'PyMuPDF Direct'}
              </span>
            </div>

            {extraction?.pages && extraction.pages.length > 0 ? (
              extraction.pages.map((p: any) => (
                <div key={p.page_number} className="border border-slate-200 rounded-lg p-3 bg-slate-50/60 space-y-1.5">
                  <div className="flex items-center justify-between text-slate-600 font-semibold text-xs border-b border-slate-200/60 pb-1">
                    <span>Page {p.page_number}</span>
                    <button
                      onClick={() => handleCopyText(p.text)}
                      className="text-[10px] text-blue-600 hover:underline flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      <span>Copy Page Text</span>
                    </button>
                  </div>
                  <pre className="font-mono text-[11px] text-slate-800 whitespace-pre-wrap leading-relaxed p-2 bg-white rounded border border-slate-200/80">
                    {p.text}
                  </pre>
                </div>
              ))
            ) : (
              <pre className="font-mono text-[11px] text-slate-800 whitespace-pre-wrap leading-relaxed p-3 bg-slate-50 rounded border border-slate-200">
                {extraction?.raw_text || 'Extracting digital text from document...'}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
