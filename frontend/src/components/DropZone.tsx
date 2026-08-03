import { useCallback, useRef, useState } from "react";

interface DropZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];

export default function DropZone({ onFileSelected, disabled }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      const isValid = ACCEPTED_EXTENSIONS.some((ext) =>
        file.name.toLowerCase().endsWith(ext)
      );
      if (!isValid) {
        alert("Only .csv and .xlsx files are supported.");
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl px-8 py-14 text-center cursor-pointer
        transition-colors
        ${isDragging ? "border-scimly-primary bg-scimly-primary/5" : "border-scimly-border"}
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:border-scimly-primary/60"}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx"
        className="hidden"
        disabled={disabled}
        onChange={(e) => handleFiles(e.target.files)}
      />
      <p className="text-scimly-text font-medium mb-1">
        Drag and drop your file here
      </p>
      <p className="text-scimly-muted text-sm mb-4">or click to browse</p>
      <p className="text-scimly-muted text-xs">Supports .csv and .xlsx, up to 50 MB</p>
    </div>
  );
}
