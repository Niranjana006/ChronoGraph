import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, useRef, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { apiFetch } from "@/lib/api";

export const Route = createFileRoute("/workspace/$workspaceId/graph")({
  component: GraphPage,
});

function GraphPage() {
  const { workspaceId } = Route.useParams();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    async function loadGraph() {
      try {
        const data = await apiFetch(`/workspaces/${workspaceId}/graph`);
        setGraphData(data);
      } catch (err) {
        console.error("Failed to load graph:", err);
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, [workspaceId]);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  const nodeColors = useMemo(() => {
    return {
      Person: "#3b82f6", // blue
      Organization: "#10b981", // green
      Location: "#ef4444", // red
      Event: "#f59e0b", // yellow
      Food: "#8b5cf6", // purple
      Product: "#ec4899", // pink
    };
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading Knowledge Graph...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4">
        <h1 className="text-lg font-semibold">Knowledge Graph</h1>
        <p className="text-sm text-muted-foreground">
          Explore the entities and facts extracted from your documents.
        </p>
      </div>
      <div className="flex-1 overflow-hidden bg-zinc-950" ref={containerRef}>
        <ForceGraph2D
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={(node: any) => (nodeColors as any)[node.type] || "#94a3b8"}
          nodeRelSize={6}
          linkColor={() => "rgba(255,255,255,0.2)"}
          linkWidth={1.5}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkLabel={(link: any) => link.label}
          backgroundColor="#09090b"
          onNodeDragEnd={(node: any) => {
            node.fx = node.x;
            node.fy = node.y;
          }}
        />
      </div>
    </div>
  );
}
