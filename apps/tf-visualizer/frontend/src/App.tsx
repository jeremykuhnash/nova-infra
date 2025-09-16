import React, { useEffect, useState } from 'react';
import createEngine, {
  DiagramModel,
  DefaultNodeModel,
  DefaultLinkModel,
} from '@projectstorm/react-diagrams';
import { CanvasWidget } from '@projectstorm/react-canvas-core';
import axios from 'axios';
import dagre from 'dagre';
import './styles.css';

interface TerraformEntity {
  id: string;
  type: string;
  category: string;
  name: string;
  provider?: string;
  attributes: any;
  dependencies: string[];
  position?: { x: number; y: number };
}

interface Relationship {
  source: string;
  target: string;
  type: string;
}

interface TerraformData {
  entities: TerraformEntity[];
  relationships: Relationship[];
  metadata: {
    total_files: number;
    total_entities: number;
    total_relationships: number;
  };
}

const App: React.FC = () => {
  const [engine] = useState(createEngine());
  const [model, setModel] = useState<DiagramModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<TerraformData['metadata'] | null>(null);
  const [originalData, setOriginalData] = useState<TerraformData | null>(null);
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR' | 'BT' | 'RL'>('TB');

  // Filter state - default to all visible for better initial view
  const [visibleCategories, setVisibleCategories] = useState<Set<string>>(
    new Set(['provider', 'resource', 'data', 'module', 'variable', 'output'])
  );

  useEffect(() => {
    loadTerraformData();
  }, []);

  // Re-render diagram when filters or layout change
  useEffect(() => {
    if (originalData) {
      renderDiagram(originalData);
    }
  }, [visibleCategories, layoutDirection]);

  const loadTerraformData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to load entities from backend
      const response = await axios.get('/api/entities');

      if (response.data.success) {
        setOriginalData(response.data.data);
        renderDiagram(response.data.data);
      } else {
        // Fall back to sample data
        const sampleResponse = await axios.get('/api/sample');
        setOriginalData(sampleResponse.data.data);
        renderDiagram(sampleResponse.data.data);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      // Try sample data as fallback
      try {
        const sampleResponse = await axios.get('/api/sample');
        setOriginalData(sampleResponse.data.data);
        renderDiagram(sampleResponse.data.data);
      } catch (sampleErr) {
        setError('Failed to load Terraform data');
      }
    } finally {
      setLoading(false);
    }
  };

  const applyDagreLayout = (
    nodes: { [key: string]: DefaultNodeModel },
    relationships: Relationship[]
  ) => {
    // Create a new directed graph
    const g = new dagre.graphlib.Graph();
    g.setGraph({
      rankdir: layoutDirection, // Use selected layout direction
      nodesep: 80, // Horizontal space between nodes
      ranksep: 120, // Vertical space between ranks
      marginx: 50,
      marginy: 50,
      edgesep: 20, // Space between edges
    });
    g.setDefaultEdgeLabel(() => ({}));

    // Add nodes to the graph
    Object.entries(nodes).forEach(([id]) => {
      g.setNode(id, { width: 150, height: 60 });
    });

    // Add edges to the graph
    relationships.forEach((rel) => {
      if (nodes[rel.source] && nodes[rel.target]) {
        g.setEdge(rel.source, rel.target);
      }
    });

    // Run the layout algorithm
    dagre.layout(g);

    // Apply the computed positions to the nodes
    g.nodes().forEach((nodeId) => {
      const nodeData = g.node(nodeId);
      const node = nodes[nodeId];
      if (node && nodeData) {
        node.setPosition(nodeData.x - 75, nodeData.y - 30); // Center the node
      }
    });
  };

  const renderDiagram = (data: TerraformData) => {
    const diagramModel = new DiagramModel();
    const nodeMap: { [key: string]: DefaultNodeModel } = {};

    setMetadata(data.metadata);

    // Filter entities based on visible categories
    const filteredEntities = data.entities.filter((entity) =>
      visibleCategories.has(entity.category)
    );

    // Create nodes for each visible entity
    filteredEntities.forEach((entity) => {
      // Build display name with type information
      let displayName = '';

      // Add resource type as the main label
      if (entity.type) {
        displayName = `[${entity.type}]\n`;
      }

      // Add the entity name
      displayName += entity.name || entity.id;

      // For outputs, add the value
      if (entity.category === 'output' && entity.attributes) {
        const value =
          entity.attributes.value ||
          entity.attributes.default ||
          entity.attributes.description ||
          '';
        if (value) {
          const cleanValue = String(value)
            .replace(/\${/g, '')
            .replace(/}/g, '')
            .replace(/"/g, '')
            .slice(0, 30); // Limit length for display
          displayName += `\n→ ${cleanValue}`;
        }
      }

      const node = new DefaultNodeModel({
        name: displayName,
        color: getNodeColor(entity.category),
      });

      // Initial position (will be updated by dagre)
      node.setPosition(100, 100);

      // Add ports
      node.addInPort('In');
      node.addOutPort('Out');

      nodeMap[entity.id] = node;
      diagramModel.addNode(node);
    });

    // Apply dagre layout to position nodes nicely
    const filteredRelationships = data.relationships.filter(
      (rel) => nodeMap[rel.source] && nodeMap[rel.target]
    );
    applyDagreLayout(nodeMap, filteredRelationships);

    // Create links for relationships (only between visible nodes)
    filteredRelationships.forEach((rel) => {
      const sourceNode = nodeMap[rel.source];
      const targetNode = nodeMap[rel.target];

      if (sourceNode && targetNode) {
        const sourcePort = sourceNode.getPort('Out');
        const targetPort = targetNode.getPort('In');

        if (sourcePort && targetPort) {
          const link = new DefaultLinkModel();
          link.setSourcePort(sourcePort);
          link.setTargetPort(targetPort);
          link.setColor('#94a3b8'); // Slate color for links
          diagramModel.addLink(link);
        }
      }
    });

    engine.setModel(diagramModel);
    setModel(diagramModel);
  };

  const getNodeColor = (category: string): string => {
    const colors: { [key: string]: string } = {
      provider: '#6366f1', // Indigo
      resource: '#10b981', // Emerald
      data: '#3b82f6', // Blue
      module: '#f59e0b', // Amber
      variable: '#8b5cf6', // Violet
      output: '#ef4444', // Red
      default: '#6b7280', // Gray
    };
    return colors[category] || colors.default;
  };

  const toggleCategory = (category: string) => {
    const newCategories = new Set(visibleCategories);
    if (newCategories.has(category)) {
      newCategories.delete(category);
    } else {
      newCategories.add(category);
    }
    setVisibleCategories(newCategories);
  };

  const showAll = () => {
    setVisibleCategories(new Set(['provider', 'resource', 'data', 'module', 'variable', 'output']));
  };

  const showMinimal = () => {
    setVisibleCategories(new Set(['output']));
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    try {
      setLoading(true);
      setError(null);
      const response = await axios.post('/api/parse', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setOriginalData(response.data.data);
        renderDiagram(response.data.data);
      }
    } catch (err) {
      setError('Failed to parse Terraform files');
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = () => {
    loadTerraformData();
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading Terraform infrastructure...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={refreshData} className="btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Terraform Infrastructure Visualizer</h1>
        <div className="controls">
          <input
            type="file"
            id="file-upload"
            multiple
            accept=".tf,.tfvars,.hcl"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <label htmlFor="file-upload" className="btn">
            Upload TF Files
          </label>
          <button onClick={refreshData} className="btn">
            Refresh
          </button>
          <button onClick={showAll} className="btn">
            Show All
          </button>
          <button onClick={showMinimal} className="btn">
            Minimal View
          </button>
          <select
            value={layoutDirection}
            onChange={(e) => setLayoutDirection(e.target.value as any)}
            className="btn"
            style={{ padding: '0.4rem 0.8rem' }}
          >
            <option value="TB">Top → Bottom</option>
            <option value="BT">Bottom → Top</option>
            <option value="LR">Left → Right</option>
            <option value="RL">Right → Left</option>
          </select>
        </div>
      </header>

      {metadata && (
        <div className="metadata">
          <span>Files: {metadata.total_files || 0}</span>
          <span>Entities: {metadata.total_entities || 0}</span>
          <span>Relationships: {metadata.total_relationships || 0}</span>
          <span>
            Visible:{' '}
            {visibleCategories.size > 0 ? Array.from(visibleCategories).join(', ') : 'none'}
          </span>
        </div>
      )}

      <div className="diagram-container">
        {model && <CanvasWidget engine={engine} className="diagram-canvas" />}
      </div>

      <div className="legend">
        <h3>Legend (Click to Filter)</h3>
        <div className="legend-items">
          <div
            className={`legend-item ${visibleCategories.has('provider') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('provider')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#6366f1' }}></span>
            Provider
          </div>
          <div
            className={`legend-item ${visibleCategories.has('resource') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('resource')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#10b981' }}></span>
            Resource
          </div>
          <div
            className={`legend-item ${visibleCategories.has('data') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('data')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#3b82f6' }}></span>
            Data Source
          </div>
          <div
            className={`legend-item ${visibleCategories.has('module') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('module')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#f59e0b' }}></span>
            Module
          </div>
          <div
            className={`legend-item ${visibleCategories.has('variable') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('variable')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#8b5cf6' }}></span>
            Variable
          </div>
          <div
            className={`legend-item ${visibleCategories.has('output') ? 'active' : 'inactive'}`}
            onClick={() => toggleCategory('output')}
            style={{ cursor: 'pointer' }}
          >
            <span className="color-box" style={{ backgroundColor: '#ef4444' }}></span>
            Output
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
