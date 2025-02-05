/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState, useEffect } from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
import * as XLSX from "https://esm.sh/xlsx";
import { Chart, registerables } from "https://esm.sh/chart.js@4.4.0";

Chart.register(...registerables);

const CHART_TYPES = [
  'bar', 
  'line', 
  'pie', 
  'scatter', 
  'radar', 
  'doughnut'
];

const CHART_COLORS = [
  'rgba(75, 192, 192, 0.6)',
  'rgba(255, 99, 132, 0.6)',
  'rgba(54, 162, 235, 0.6)',
  'rgba(255, 206, 86, 0.6)',
  'rgba(153, 102, 255, 0.6)'
];

function GraphVisualization({ data, xAxis, yAxis, chartType }) {
  const chartRef = React.useRef(null);
  const [chartInstance, setChartInstance] = React.useState(null);

  React.useEffect(() => {
    if (chartRef.current && data && xAxis && yAxis) {
      // Destroy existing chart
      if (chartInstance) {
        chartInstance.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      
      // Prepare data with type conversion and filtering
      const preparedData = data.map(item => ({
        x: item[xAxis],
        y: Number(item[yAxis]) // Ensure numeric conversion
      })).filter(item => !isNaN(item.y)); // Remove non-numeric values

      console.log('Prepared Data:', preparedData); // Debug log

      const chartConfig = {
        type: chartType,
        data: {
          labels: preparedData.map(item => item.x),
          datasets: [{
            label: yAxis,
            data: preparedData.map(item => item.y),
            backgroundColor: CHART_COLORS,
            borderColor: 'rgba(0,0,0,0.1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: chartType !== 'pie' && chartType !== 'doughnut' ? {
            x: {
              type: 'category',
              title: {
                display: true,
                text: xAxis
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: yAxis
              }
            }
          } : {}
        }
      };

      try {
        const newChartInstance = new Chart(ctx, chartConfig);
        setChartInstance(newChartInstance);
      } catch (error) {
        console.error('Chart Creation Error:', error);
      }
    }
  }, [data, xAxis, yAxis, chartType]);

  // Add error boundary
  if (!data || !xAxis || !yAxis) {
    return <div>Please select X and Y axes</div>;
  }

  return (
    <div className="chart-container">
      <h3>{`${chartType.toUpperCase()} Chart: ${xAxis} vs ${yAxis}`}</h3>
      <canvas ref={chartRef}></canvas>
    </div>
  );
}

function App() {
  const [fileData, setFileData] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [graphConfigs, setGraphConfigs] = useState([]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    
    reader.onload = async (event) => {
      const workbook = XLSX.read(event.target.result, { type: 'binary' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const data = XLSX.utils.sheet_to_json(worksheet, { 
        raw: false, // Convert all values to strings
        defval: null 
      });
      
      const response = await fetch('/analyze', {
        method: 'POST',
        body: JSON.stringify(data)
      });
      
      const results = await response.json();
      setFileData(data);
      setAnalysisResults(results);
      
      // Initialize with one default graph config
      setGraphConfigs([{
        xAxis: results.columns[0] || null,
        yAxis: results.numericColumns[0] || null,
        chartType: 'bar'
      }]);
    };
    
    reader.readAsBinaryString(file);
  };

  const addGraphConfig = () => {
    setGraphConfigs(prev => [...prev, {
      xAxis: analysisResults?.columns[0] || null,
      yAxis: analysisResults?.numericColumns[0] || null,
      chartType: 'bar'
    }]);
  };

  const updateGraphConfig = (index, updates) => {
    setGraphConfigs(prev => 
      prev.map((config, i) => 
        i === index ? { ...config, ...updates } : config
      )
    );
  };

  const removeGraphConfig = (index) => {
    setGraphConfigs(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="container">
      <h1>📊 Excel Data Analysis Dashboard</h1>
      <input 
        type="file" 
        accept=".xlsx, .xls" 
        onChange={handleFileUpload} 
      />
      
      {analysisResults && (
        <div className="dashboard">
          <h2>Analysis Results</h2>
          <div className="stats">
            <div>Total Rows: {analysisResults.totalRows}</div>
            <div>Columns: {analysisResults.columns.join(", ")}</div>
            <div>Numeric Columns: {analysisResults.numericColumns.join(", ")}</div>
          </div>
          
          <button onClick={addGraphConfig} className="add-graph-btn">
            + Add Graph
          </button>

          <div className="graphs-container">
            {graphConfigs.map((config, index) => (
              <div key={index} className="graph-config">
                <div className="graph-controls">
                  <select 
                    value={config.xAxis || ''} 
                    onChange={(e) => updateGraphConfig(index, { xAxis: e.target.value })}
                  >
                    <option value="">Select X-Axis</option>
                    {analysisResults.columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>

                  <select 
                    value={config.yAxis || ''} 
                    onChange={(e) => updateGraphConfig(index, { yAxis: e.target.value })}
                  >
                    <option value="">Select Y-Axis</option>
                    {analysisResults.numericColumns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>

                  <select 
                    value={config.chartType} 
                    onChange={(e) => updateGraphConfig(index, { chartType: e.target.value })}
                  >
                    {CHART_TYPES.map(type => (
                      <option key={type} value={type}>{type.toUpperCase()}</option>
                    ))}
                  </select>

                  <button onClick={() => removeGraphConfig(index)}>🗑️</button>
                </div>

                {config.xAxis && config.yAxis && (
                  <GraphVisualization 
                    data={fileData} 
                    xAxis={config.xAxis} 
                    yAxis={config.yAxis} 
                    chartType={config.chartType}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="summary">
            <h3>Summary Statistics</h3>
            {Object.entries(analysisResults.summaryStats).map(([key, value]) => (
              <div key={key}>
                {key}: {JSON.stringify(value)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function client() {
  createRoot(document.getElementById("root")).render(<App />);
}
if (typeof document !== "undefined") { client(); }

export default async function server(request: Request): Promise<Response> {
  if (request.method === 'POST' && new URL(request.url).pathname === '/analyze') {
    const data = await request.json();
    
    const analysis = {
      totalRows: data.length,
      columns: Object.keys(data[0] || {}),
      numericColumns: Object.keys(data[0] || {}).filter(key => {
        // Improved numeric column detection
        const values = data.map(row => row[key]);
        return values.some(value => 
          value !== null && 
          value !== undefined && 
          !isNaN(Number(value))
        );
      }),
      summaryStats: calculateSummaryStats(data)
    };
    
    return new Response(JSON.stringify(analysis), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  return new Response(`
    <html>
      <head>
        <title>Excel Data Dashboard</title>
        <style>${css}</style>
      </head>
      <body>
        <div id="root"></div>
        <script src="https://esm.town/v/std/catch"></script>
        <script type="module" src="${import.meta.url}"></script>
      </body>
    </html>
  `, {
    headers: { 'Content-Type': 'text/html' }
  });
}

function calculateSummaryStats(data) {
  const stats = {};
  
  Object.keys(data[0] || {}).forEach(key => {
    // Improved numeric value filtering and conversion
    const values = data
      .map(row => Number(row[key]))
      .filter(v => !isNaN(v));
    
    if (values.length > 0) {
      stats[key] = {
        min: Math.min(...values),
        max: Math.max(...values),
        average: values.reduce((a, b) => a + b, 0) / values.length,
        count: values.length
      };
    }
  });
  
  return stats;
}

const css = `
body { 
  font-family: Arial, sans-serif; 
  max-width: 1200px; 
  margin: 0 auto; 
  padding: 20px;
}
.container {
  text-align: center;
}
.dashboard {
  margin-top: 20px;
  text-align: left;
}
.stats, .summary {
  background: #f4f4f4;
  padding: 15px;
  border-radius: 5px;
  margin: 10px 0;
}
input[type="file"] {
  margin: 20px 0;
}
.graph-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0;
  gap: 10px;
}
.graph-controls select {
  flex-grow: 1;
  padding: 10px;
}
.graphs-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}
.chart-container {
  width: 100%;
  height: 400px;
  border: 1px solid #e0e0e0;
  padding: 10px;
  border-radius: 5px;
}
.add-graph-btn {
  margin: 15px 0;
  padding: 10px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
.graph-config {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 5px;
}
`;
