import React, { useEffect, useState } from 'react';
import createEngine, {
  DiagramModel,
  DefaultNodeModel,
  DefaultLinkModel,
} from '@projectstorm/react-diagrams';
import { CanvasWidget } from '@projectstorm/react-canvas-core';
import axios from 'axios';
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

  // Filter state - default to only outputs visible
  const [visibleCategories, setVisibleCategories] = useState<Set<string>>(
    new Set(['output'])
  );

  useEffect(() => {
    loadTerraformData();
  }, []);

  // Re-render diagram when filters change
  useEffect(() => {
    if (originalData) {
      renderDiagram(originalData);
    }
  }, [visibleCategories]);

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

  const renderDiagram = (data: TerraformData) => {
    const diagramModel = new DiagramModel();
    const nodeMap: { [key: string]: DefaultNodeModel } = {};

    setMetadata(data.metadata);

    // Filter entities based on visible categories
    const filteredEntities = data.entities.filter(entity =>
      visibleCategories.has(entity.category)
    );

    // Create nodes for each visible entity
    filteredEntities.forEach((entity) => {
      // For outputs, try to get the value from attributes
      let displayName = entity.id;
      if (entity.category === 'output' && entity.attributes) {
        // Check for common value patterns in output attributes
        const value = entity.attributes.value ||
                     entity.attributes.default ||
                     entity.attributes.description ||
                     '';
        if (value) {
          // Extract the actual value if it's a reference
          const cleanValue = String(value)
            .replace(/\${/g, '')
            .replace(/}/g, '')
            .replace(/"/g, '');

          // Show both the output name and its value
          displayName = `${entity.id}\n${cleanValue}`;
        }
      }

      const node = new DefaultNodeModel({
        name: displayName,
        color: getNodeColor(entity.category),
      });

      // Position the node
      if (entity.position) {
        node.setPosition(entity.position.x, entity.position.y);
      } else {
        // Default positioning if not provided - arrange by category
        const categoryIndex = Array.from(visibleCategories).indexOf(entity.category);
        const entityIndex = filteredEntities.filter(e => e.category === entity.category).indexOf(entity);
        const x = 100 + (categoryIndex * 200) + (entityIndex % 3) * 150;
        const y = 100 + Math.floor(entityIndex / 3) * 150;
        node.setPosition(x, y);
      }

      // Add ports
      node.addInPort('In');
      node.addOutPort('Out');

      nodeMap[entity.id] = node;
      diagramModel.addNode(node);
    });

    // Create links for relationships (only between visible nodes)
    data.relationships.forEach((rel) => {
      const sourceNode = nodeMap[rel.source];
      const targetNode = nodeMap[rel.target];

      if (sourceNode && targetNode) {
        const sourcePort = sourceNode.getPort('Out');
        const targetPort = targetNode.getPort('In');

        if (sourcePort && targetPort) {
          const link = new DefaultLinkModel();
          link.setSourcePort(sourcePort);
          link.setTargetPort(targetPort);
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
        </div>
      </header>

      {metadata && (
        <div className="metadata">
          <span>Files: {metadata.total_files || 0}</span>
          <span>Entities: {metadata.total_entities || 0}</span>
          <span>Relationships: {metadata.total_relationships || 0}</span>
          <span>Visible: {visibleCategories.size > 0 ? Array.from(visibleCategories).join(', ') : 'none'}</span>
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
