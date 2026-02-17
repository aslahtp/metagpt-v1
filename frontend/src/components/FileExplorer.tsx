"use client";

import { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  File,
  Folder,
  FolderOpen,
} from "lucide-react";
import { useProjectStore } from "@/lib/store";
import { cn, getLanguageFromPath, getFileIcon } from "@/lib/utils";
import type { FileTreeNode } from "@/lib/api";

interface FileExplorerProps {
  onSelectFile: (path: string) => void;
}

export function FileExplorer({ onSelectFile }: FileExplorerProps) {
  const { fileTree, selectedFile, generatedFiles, hideNodeModules } =
    useProjectStore();

  if (!fileTree && generatedFiles.length === 0) {
    return (
      <div className="p-4 text-center text-foreground-muted text-sm">
        <p>No files generated yet.</p>
        <p className="text-xs mt-1">
          Files will appear here after the Engineer agent runs.
        </p>
      </div>
    );
  }

  // Build tree from generated files if no file tree
  const tree = fileTree || buildTreeFromFiles(generatedFiles);

  // Render children of root directly (skip the root "files" wrapper)
  const children = tree?.children ?? [];

  return (
    <div className="py-2">
      {children
        .sort((a, b) => {
          if (a.type !== b.type) return a.type === "directory" ? -1 : 1;
          return a.name.localeCompare(b.name);
        })
        .map((child) => (
          <TreeNode
            key={child.path}
            node={child}
            selectedPath={selectedFile}
            onSelect={onSelectFile}
            depth={0}
            hideNodeModules={hideNodeModules}
          />
        ))}
    </div>
  );
}

interface TreeNodeProps {
  node: FileTreeNode;
  selectedPath: string | null;
  onSelect: (path: string) => void;
  depth: number;
  hideNodeModules: boolean;
}

function TreeNode({ node, selectedPath, onSelect, depth, hideNodeModules }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);

  const isDirectory = node.type === "directory";
  const isSelected = node.path === selectedPath;

  // Skip node_modules directories when hidden
  if (hideNodeModules && isDirectory && node.name === "node_modules") {
    return null;
  }

  const handleClick = () => {
    if (isDirectory) {
      setExpanded(!expanded);
    } else {
      onSelect(node.path);
    }
  };

  const language = !isDirectory ? getLanguageFromPath(node.name) : null;

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          "w-full flex items-center gap-1.5 px-2 py-1 text-left text-sm hover:bg-background-tertiary transition-colors",
          isSelected && "bg-accent/10 text-accent",
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isDirectory ? (
          <>
            {expanded ? (
              <ChevronDown className="h-4 w-4 shrink-0 text-foreground-subtle" />
            ) : (
              <ChevronRight className="h-4 w-4 shrink-0 text-foreground-subtle" />
            )}
            {expanded ? (
              <FolderOpen className="h-4 w-4 shrink-0 text-accent" />
            ) : (
              <Folder className="h-4 w-4 shrink-0 text-accent" />
            )}
          </>
        ) : (
          <>
            <span className="w-4" />
            <span className="text-xs">
              {language ? getFileIcon(language) : "📄"}
            </span>
          </>
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {isDirectory && expanded && node.children && (
        <div>
          {node.children
            .sort((a, b) => {
              // Directories first, then files
              if (a.type !== b.type) {
                return a.type === "directory" ? -1 : 1;
              }
              return a.name.localeCompare(b.name);
            })
            .map((child) => (
              <TreeNode
                key={child.path}
                node={child}
                selectedPath={selectedPath}
                onSelect={onSelect}
                depth={depth + 1}
                hideNodeModules={hideNodeModules}
              />
            ))}
        </div>
      )}
    </div>
  );
}

// Build tree from flat file list
function buildTreeFromFiles(
  files: { file_path: string }[],
): FileTreeNode | null {
  if (files.length === 0) return null;

  const root: FileTreeNode = {
    name: "files",
    path: "/",
    type: "directory",
    children: [],
  };

  for (const file of files) {
    const parts = file.file_path.split("/").filter(Boolean);
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      const path = parts.slice(0, i + 1).join("/");

      let child = current.children?.find((c) => c.name === part);

      if (!child) {
        child = {
          name: part,
          path,
          type: isFile ? "file" : "directory",
          children: isFile ? [] : [],
        };
        current.children = current.children || [];
        current.children.push(child);
      }

      current = child;
    }
  }

  return root;
}
