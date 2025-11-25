"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Save, X } from "lucide-react";
import ReactFlow, {
  type Node,
  type Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  Handle,
  Position,
  Background,
  Controls,
  MiniMap,
} from "reactflow";
import "reactflow/dist/style.css";

interface DataContent {
  label: string;
  head: string[];
  rows: string[][];
}

interface RequiredField {
  name: string;
  type: string;
  description?: string;
}

interface RequiredData {
  fields: RequiredField[];
}

interface ColumnMapping {
  [requiredCol: string]: string | null;
}

// helper to produce safe ids from column names
const idFromCol = (prefix: string, col: string) =>
  `${prefix}-${col
    .replace(/\s+/g, "_")
    .replace(/[^a-zA-Z0-9_\-]/g, "")
    .toLowerCase()}`;

// simple heuristic to infer column type from sample values
const inferColumnType = (values: string[]): string => {
  const nonNull = values.filter(
    (v) => v !== null && v !== undefined && v !== ""
  );
  if (nonNull.length === 0) return "unknown";

  const isNumber = nonNull.every(
    (v) => !isNaN(Number(String(v).replace(/,/g, "")))
  );
  if (isNumber) return "number";

  const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  const isEmail = nonNull.every((v) => emailRegex.test(String(v)));
  if (isEmail) return "email";

  const isDate = nonNull.every((v) => !isNaN(Date.parse(String(v))));
  if (isDate) return "date";

  return "string";
};

// Custom node component for source columns
function SourceColumnNode({
  data,
}: {
  data: { label: string; samples: string[]; inferredType: string };
}) {
  return (
    <div className="w-56 rounded-lg border-2 border-blue-500 bg-blue-50 p-3 text-xs shadow-sm dark:bg-blue-950/30">
      <p className="mb-1 text-sm font-semibold text-blue-700 dark:text-blue-400">
        {data.label}
      </p>
      <div className="mb-1">
        <p className="font-medium text-[11px] uppercase tracking-wide text-blue-800/80 dark:text-blue-300/80">
          Samples
        </p>
        <ul className="max-h-16 list-disc space-y-0.5 overflow-y-auto pl-4">
          {data.samples.map((s, i) => (
            <li
              key={i}
              className="truncate text-[11px] text-blue-900 dark:text-blue-100"
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-1 text-[11px] text-blue-900/80 dark:text-blue-200/80">
        Type: <span className="font-semibold">{data.inferredType}</span>
      </p>
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-2! w-2! bg-blue-500!"
      />
    </div>
  );
}

// Custom node component for required fields
function TargetColumnNode({
  data,
}: {
  data: {
    label: string;
    requiredType?: string;
    mapped: boolean;
    description?: string;
  };
}) {
  return (
    <div
      className={`w-64 rounded-lg border-2 p-3 text-xs shadow-sm ${
        data.mapped
          ? "border-green-500 bg-green-50 dark:bg-green-950/30"
          : "border-dashed border-muted-foreground/50 bg-muted/30"
      }`}
    >
      <p className="mb-1 text-sm font-semibold">{data.label}</p>
      {data.requiredType && (
        <p className="text-[11px] text-muted-foreground">
          Required type:{" "}
          <span className="font-semibold">{data.requiredType}</span>
        </p>
      )}
      {data.description && (
        <p className="mt-1 line-clamp-2 text-[11px] text-muted-foreground">
          {data.description}
        </p>
      )}
      <div className="mt-2 flex items-center justify-between text-[11px]">
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
            data.mapped
              ? "bg-green-500/10 text-green-700 dark:text-green-300"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {data.mapped ? "Mapped" : "Not mapped"}
        </span>
      </div>
      <Handle type="target" position={Position.Top} className="h-2! w-2!" />
    </div>
  );
}

export default function DetailPage() {
  const [dataContent] = useState<DataContent>({
    label: "Sample Dataset",
    head: ["User ID", "Name", "Email", "Age", "Department", "Salary"],
    rows: [
      ["1", "John Doe", "john@example.com", "28", "Engineering", "75000"],
      ["2", "Jane Smith", "jane@example.com", "32", "Marketing", "65000"],
      ["3", "Bob Johnson", "bob@example.com", "35", "Sales", "70000"],
      ["4", "Alice Brown", "alice@example.com", "29", "Engineering", "78000"],
      ["5", "Charlie Wilson", "charlie@example.com", "31", "HR", "60000"],
    ],
  });

  const [requiredData] = useState<RequiredData>({
    fields: [
      {
        name: "Employee ID",
        type: "number",
        description: "Unique identifier for each employee",
      },
      {
        name: "Full Name",
        type: "string",
        description: "Employee's full name",
      },
      {
        name: "Contact Email",
        type: "email",
        description: "Primary email for communication",
      },
      {
        name: "Years Experience",
        type: "number",
        description: "Total years of work experience",
      },
    ],
  });

  const [mapping, setMapping] = useState<ColumnMapping>(() => {
    const initial: ColumnMapping = {};
    for (const f of [
      "Employee ID",
      "Full Name",
      "Contact Email",
      "Years Experience",
    ]) {
      initial[f] = null;
    }
    return initial;
  });

  // Build initial nodes: show dataset columns with samples & inferred type, and required fields on the right
  const initialNodes: Node[] = useMemo(() => {
    const sourceNodes: Node[] = dataContent.head.map((col, idx) => {
      const colIndex = dataContent.head.indexOf(col);
      const samples = dataContent.rows
        .map((row) => row[colIndex])
        .filter((v) => v !== undefined && v !== null && v !== "")
        .slice(0, 4)
        .map((v) => String(v));

      const inferredType = inferColumnType(samples);

      return {
        id: idFromCol("source", col),
        data: { label: col, samples, inferredType },
        position: { x: idx * 250, y: 0 },
        type: "sourceColumn",
      };
    });

    const targetNodes: Node[] = requiredData.fields.map((field, idx) => ({
      id: idFromCol("target", field.name),
      data: {
        label: field.name,
        requiredType: field.type,
        description: field.description,
        mapped: false,
      },
      position: { x: idx * 300, y: 350 },
      type: "targetColumn",
    }));

    return [...sourceNodes, ...targetNodes];
  }, [dataContent.head, dataContent.rows, requiredData.fields]);

  const initialEdges: Edge[] = useMemo(
    () =>
      Object.entries(mapping)
        .filter(([, sourceCol]) => sourceCol !== null)
        .map(([targetCol, sourceCol]) => ({
          id: `edge-${idFromCol("source", sourceCol as string)}-${idFromCol(
            "target",
            targetCol
          )}`,
          source: idFromCol("source", sourceCol as string),
          target: idFromCol("target", targetCol),
          animated: true,
        })),
    [mapping]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync target node `mapped` flag with mapping state
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        if (!node.id.startsWith("target-")) return node;

        const field = requiredData.fields.find(
          (f) => idFromCol("target", f.name) === node.id
        );
        if (!field) return node;

        const isMapped = mapping[field.name] !== null;
        return { ...node, data: { ...node.data, mapped: isMapped } };
      })
    );
  }, [mapping, requiredData.fields, setNodes]);

  const nodeTypes = useMemo(
    () => ({
      sourceColumn: SourceColumnNode,
      targetColumn: TargetColumnNode,
    }),
    []
  );

  // onConnect: add / update mapping and edge
  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;

      const sourceId = connection.source;
      const targetId = connection.target;

      const sourceCol = dataContent.head.find(
        (h) => idFromCol("source", h) === sourceId
      );
      const targetField = requiredData.fields.find(
        (f) => idFromCol("target", f.name) === targetId
      );
      if (!sourceCol || !targetField) return;

      // update mapping: ensure 1:1 from source to target (a source chỉ map 1 field)
      setMapping((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((k) => {
          if (next[k] === sourceCol) next[k] = null;
        });
        next[targetField.name] = sourceCol;
        return next;
      });

      // update edges
      setEdges((eds) => {
        const withoutTarget = eds.filter((e) => e.target !== targetId);
        const newEdge: Edge = {
          id: `edge-${sourceId}-${targetId}`,
          source: sourceId,
          target: targetId,
          animated: true,
        };
        return addEdge(newEdge as Edge, withoutTarget);
      });
    },
    [dataContent.head, requiredData.fields, setEdges]
  );

  // onEdgesDelete: clear mapping when edge removed
  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      if (!deleted || deleted.length === 0) return;

      setMapping((prev) => {
        const next = { ...prev };
        deleted.forEach((edge) => {
          const field = requiredData.fields.find(
            (f) => idFromCol("target", f.name) === edge.target
          );
          if (field) next[field.name] = null;
        });
        return next;
      });

      setEdges((eds) => eds.filter((e) => !deleted.find((d) => d.id === e.id)));
    },
    [requiredData.fields, setEdges]
  );

  // Clear mapping from summary panel
  const clearMapping = useCallback(
    (requiredCol: string) => {
      const targetId = idFromCol("target", requiredCol);
      setEdges((eds) => eds.filter((e) => e.target !== targetId));
      setMapping((prev) => ({ ...prev, [requiredCol]: null }));
    },
    [setEdges]
  );

  const saveMapping = useCallback(() => {
    console.log("Saved mapping:", mapping);
    // place to call API later
  }, [mapping]);

  return (
    <main className="min-h-screen bg-background">
      <div className="border-b bg-card">
        <div className="container mx-auto flex items-center gap-4 p-4">
          <Button variant="ghost" size="icon" asChild>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">
              Dataset Detail & Column Mapping
            </h1>
            <p className="text-sm text-muted-foreground">
              Visualize your dataset columns with sample rows and map them to
              required fields.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6 p-6">
        {/* ReactFlow Column Mapping */}
        <div className="container mx-auto">
          <Card className="h-[80vh]">
            <CardHeader className="pb-3">
              <CardTitle>Column Mapping (Interactive)</CardTitle>
              <CardDescription>
                Left: dataset columns with sample values. Right: required
                fields. Drag from source to target to map.
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[430px] p-0">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onEdgesDelete={onEdgesDelete}
                nodeTypes={nodeTypes}
                fitView
                proOptions={{ hideAttribution: true }}
              >
                <Background />
                <MiniMap />
                <Controls />
              </ReactFlow>
            </CardContent>
          </Card>
        </div>

        {/* Data Preview Section */}
        <div className="container mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Data Preview</CardTitle>
              <CardDescription>{dataContent.label}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      {dataContent.head.map((column) => (
                        <th
                          key={column}
                          className="px-4 py-2 text-left font-semibold text-muted-foreground"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dataContent.rows.slice(0, 5).map((row, idx) => (
                      <tr key={idx} className="border-b last:border-0">
                        {row.map((cell, cellIdx) => (
                          <td key={cellIdx} className="px-4 py-2">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {dataContent.rows.length > 5 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    ... and {dataContent.rows.length - 5} more rows
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mapping Summary */}
        <div className="container mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Mapping Summary</CardTitle>
              <CardDescription>
                Review which required fields are already mapped to dataset
                columns.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {requiredData.fields.map((field) => {
                  const mapped = mapping[field.name];
                  return (
                    <div
                      key={field.name}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div>
                        <p className="text-sm font-medium">{field.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {mapped ? `Mapped to: ${mapped}` : "Not mapped"}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-3 w-3 rounded-full ${
                            mapped ? "bg-green-500" : "bg-gray-300"
                          }`}
                        ></div>
                        {mapped && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => clearMapping(field.name)}
                            className="h-6 w-6 p-0"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button variant="outline">Cancel</Button>
                <Button onClick={saveMapping}>
                  <Save className="mr-2 h-4 w-4" />
                  Save Mapping
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
