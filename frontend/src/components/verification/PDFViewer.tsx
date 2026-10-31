import React, { useState } from 'react';
import { FileText, ExternalLink, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { documentsService } from '../../services/documents.service';

interface PDFViewerProps {
  documentId?: string;
  filename?: string;
  highlightPage?: number | null;
  highlightText?: string | null;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  documentId,
  filename = 'Document',
  highlightPage,
  highlightText,
}) => {
  const [zoomLevel, setZoomLevel] = useState(100);

  if (!documentId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-200 rounded-xl text-center">
        <FileText className="w-12 h-12 text-slate-300 mb-3" />
        <p className="text-sm font-semibold text-slate-600">No Document Selected</p>
        <p className="text-xs text-slate-400 mt-1">
          Select a commercial document to view its digital PDF pages and source evidence.
        </p>
      </div>
    );
  }

  const fileUrl = documentsService.getDocumentFileUrl(documentId);
  const pdfWithPage = highlightPage ? `${fileUrl}#page=${highlightPage}` : fileUrl;

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 20, 200));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 20, 60));
  const handleResetZoom = () => setZoomLevel(100);

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-subtle">
      {/* Viewer Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
          <span className="font-semibold text-slate-800 truncate" title={filename}>
            {filename}
          </span>
          {highlightPage && (
            <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium text-[11px]">
              Page {highlightPage}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono text-slate-500 w-10 text-center">
            {zoomLevel}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-px bg-slate-300 mx-1" />

          <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600 inline-flex items-center"
            title="Open in new window"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <a
            href={fileUrl}
            download={filename}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-600 inline-flex items-center"
            title="Download PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Traceable Source Text Banner if inspecting a specific discrepancy */}
      {highlightText && (
        <div className="px-4 py-2 bg-amber-50/80 border-b border-amber-200/80 flex items-start gap-2 text-xs">
          <span className="font-semibold text-amber-900 shrink-0">Source Evidence:</span>
          <code className="text-amber-800 bg-amber-100/70 px-1.5 py-0.5 rounded font-mono text-[11px] break-all">
            "{highlightText}"
          </code>
        </div>
      )}

      {/* PDF Stream Frame */}
      <div className="flex-1 w-full h-full min-h-[480px] bg-slate-100 relative overflow-hidden flex items-center justify-center">
        <iframe
          src={pdfWithPage}
          title={filename}
          className="w-full h-full border-none transition-transform origin-top"
          style={{ transform: `scale(${zoomLevel / 100})` }}
        />
      </div>
    </div>
  );
};

