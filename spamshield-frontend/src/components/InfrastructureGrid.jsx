import React from 'react';

const InfrastructureGrid = () => {
  // Define the full grid layout optimized for connections
  // Layout designed so connected services are adjacent
  const gridLayout = [
    [null,'lambda-predict','s3-logs'],
    ['lambda-api', null,null,'webhook'],
    [null, null,null,'postgres'],
    ['groupme', 'ec2-platform',null, ],
    [null,null, 'workers','redis']
  ];

  // Map service IDs to their full data
  const serviceData = {
    'groupme': { id: 'groupme', title: 'GroupMe', subtitle: 'Message Received', connections: ['webhook', 'lambda-api'], type: 'source' },
    'webhook': { id: 'webhook', title: 'Webhook', subtitle: 'Message Captured', connections: ['lambda-api', 'ec2-platform'], type: 'gateway' },
    'postgres': { id: 'postgres', title: 'PostgreSQL', subtitle: 'Database', connections: ['ec2-platform', 'redis'], type: 'database' },
    'lambda-api': { id: 'lambda-api', title: 'AWS Lambda', subtitle: 'API Gateway', connections: ['lambda-predict', 'ec2-platform', 's3-logs'], type: 'compute' },
    'ec2-platform': { id: 'ec2-platform', title: 'EC2 Platform', subtitle: 'Orchestrator', connections: ['postgres', 'redis', 'workers'], type: 'platform' },
    'redis': { id: 'redis', title: 'Redis', subtitle: 'Cache & Pub/Sub', connections: ['ec2-platform', 'postgres', 'workers'], type: 'cache' },
    'lambda-predict': { id: 'lambda-predict', title: 'Lambda Predict', subtitle: 'AI Analysis', connections: ['lambda-api', 'ec2-platform'], type: 'ai' },
    'workers': { id: 'workers', title: 'Worker Processes', subtitle: 'Multi-Group Monitor', connections: ['ec2-platform', 'redis'], type: 'worker' },
    's3-logs': { id: 's3-logs', title: 'S3 Logs', subtitle: 'Uptime History', connections: ['lambda-api'], type: 'storage' },
  };

  // Manual absolute connections rendered as independent SVG paths (edit freely)
  // Coordinate space matches the SVG viewBox below (0..500)
  const manualConnections = [
    // Example: Right-then-down with a curved corner (Stripe style)
    { id: 'example-lambda-to-webhook', d: 'M120,120 L200,120 Q250,120 250,160 L250,390', color: '#8B5CF6' },
  ];
  const connections = manualConnections;

  return (
    <div className="p-8 mb-16">
      {/* Stripe-style Layout: Text Left, Grid Right */}
      <div className="flex flex-col lg:flex-row lg:items-center gap-12 lg:gap-16">
        
        {/* Left Side - Text Content */}
        <div className="lg:w-1/2">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
            SpamShield Architecture
          </h2>
          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            Our distributed system combines AWS Lambda for serverless processing, 
            EC2 for persistent orchestration, and multiple interconnected services 
            for robust spam detection across multiple GroupMe communities.
          </p>
          
          {/* Architecture Features */}
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <h4 className="font-semibold text-gray-900">Serverless Processing</h4>
                <p className="text-sm text-gray-600">AWS Lambda handles API requests and AI predictions</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <h4 className="font-semibold text-gray-900">Multi-Service Orchestration</h4>
                <p className="text-sm text-gray-600">EC2 platform coordinates workers, database, and cache</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <h4 className="font-semibold text-gray-900">Scalable Infrastructure</h4>
                <p className="text-sm text-gray-600">PostgreSQL, Redis, and S3 provide persistent storage and caching</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Architecture Diagram */}
        <div className="lg:w-1/2">
          <div className="relative bg-transparent rounded-xl p-8">
            {/* Grid Container */}
            <div 
              className="w-full h-[500px] relative"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gridTemplateRows: 'repeat(4, 1fr)',
                gap: '16px'
              }}
            >
              {/* Connection Lines */}
              <svg
                width="100%" 
                height="100%"
                className="absolute inset-0 pointer-events-none"
                style={{ zIndex: 1 }}
                viewBox="0 0 500 500"
              >
                {connections.map((conn, index) => (
                  <path
                    key={conn.id || index}
                    d={conn.d}
                    stroke={conn.color || '#8B5CF6'}
                    strokeWidth="8"
                    strokeOpacity="0.5"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ))}
              </svg>
              
              {/* Grid Cells - Render all cells, including empty ones */}
              {gridLayout.map((row, rowIndex) => 
                row.map((serviceId, colIndex) => (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className="flex items-center justify-center"
                    style={{
                      gridRow: rowIndex + 1,
                      gridColumn: colIndex + 1,
                      zIndex: 2
                    }}
                  >
                    {serviceId ? (
                      <div className="bg-white border border-gray-300 rounded-lg shadow-md p-2 w-24 h-24 flex flex-col items-center justify-center hover:shadow-lg transition-all duration-200">
                        <h3 className="text-xs font-semibold text-black mb-1 leading-tight text-center">
                          {serviceData[serviceId].title}
                        </h3>
                        <p className="text-xs text-gray-600 leading-tight text-center">
                          {serviceData[serviceId].subtitle}
                        </p>
                      </div>
                    ) : (
                      <div className="w-24 h-24" /> // Empty cell - perfect square
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfrastructureGrid;
