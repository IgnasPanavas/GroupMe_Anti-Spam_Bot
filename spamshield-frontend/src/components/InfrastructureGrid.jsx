import React, { useState, useRef, useEffect, useMemo } from 'react';

const InfrastructureGrid = () => {
  // Define the full grid layout optimized for connections
  // Layout designed so connected services are adjacent
  const gridLayout = [
    [null,'lambda-predict','s3-logs'],
    ['lambda-api', null,null,'ML Model'],
    [null, null,null,'postgres'],
    ['groupme', 'ec2-platform',null, ],
    [null,null, 'workers','redis']
  ];

  // Map service IDs to their full data
  const serviceData = {
    'groupme': { id: 'groupme', title: 'GroupMe', subtitle: 'Message Received', connections: ['webhook', 'lambda-api'], type: 'source' },
    'ML Model': { id: 'ML Model', title: 'ML Model', subtitle: 'Predict Spam', connections: ['lambda-api', 'ec2-platform'], type: 'gateway' },
    'postgres': { id: 'postgres', title: 'PostgreSQL', subtitle: 'Database', connections: ['ec2-platform', 'redis'], type: 'database' },
    'lambda-api': { id: 'lambda-api', title: 'AWS Lambda', subtitle: 'API Gateway', connections: ['lambda-predict', 'ec2-platform', 's3-logs'], type: 'compute' },
    'ec2-platform': { id: 'ec2-platform', title: 'EC2 Platform', subtitle: 'Orchestrator', connections: ['postgres', 'redis', 'workers'], type: 'platform' },
    'redis': { id: 'redis', title: 'Redis', subtitle: 'Cache & Pub/Sub', connections: ['ec2-platform', 'postgres', 'workers'], type: 'cache' },
    'lambda-predict': { id: 'lambda-predict', title: 'Lambda Predict', subtitle: 'AI Analysis', connections: ['lambda-api', 'ec2-platform'], type: 'ai' },
    'workers': { id: 'workers', title: 'Worker Processes', subtitle: 'Multi-Group Monitor', connections: ['ec2-platform', 'redis'], type: 'worker' },
    's3-logs': { id: 's3-logs', title: 'S3 Logs', subtitle: 'Uptime History', connections: ['lambda-api'], type: 'storage' },
  };

  // Static connections with proper positioning - memoized to prevent infinite loops
  const staticConnections = useMemo(() => [
    {
      id: 'lambda-api-to-lambda-predict',
      d: 'M96,160 L140,160 A20,20 0 0,0 156,140 L156,30', // From AWS Lambda (top) to Lambda Predict (bottom)
      gradientId: 'lambda-api-predict-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'lambda-api-to-s3-logs',
      d: 'M96,168 L252,168 A20,20 0 0,0 272,148 L272,30', // From AWS Lambda (top) to S3 Logs (bottom)
      gradientId: 'lambda-api-s3-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'lambda-predict-to-ML Model',
      d: 'M164,96 L164,140 A20,20 0 0,0 184,156 L336,156', // From AWS Lambda (right) to ML Model (left)
      gradientId: 'lambda-predict-ml-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'lambda-api-to-ec2-platform',
      d: 'M96,176 L136,176 A20,20 0 0,1 156,196 L156,335', // From AWS Lambda (top) to EC2 Platform (bottom)
      gradientId: 'lambda-api-ec2-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'groupme-to-ec2-platform',
      d: 'M52,335 L52,292 A20,20 0 0,1 72,272 L128,272 A20,20 0 0,1 148,292 L148,335', // From GroupMe (right) to EC2 Platform (left)
      gradientId: 'groupme-ec2-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'ec2-platform-to-postgres',
      d: 'M164,335 L164,292 A20,20 0 0,1 184,272 L480,272', // From EC2 Platform (top) to PostgreSQL (left)
      gradientId: 'ec2-postgres-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'workers-to-ML-Model',
      d: 'M272,448 L272,184 A20,20 0 0,1 292,164 L336,164', // From EC2 Platform (top) to ML Model (left)
      gradientId: 'workers-ml-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'ec2-platform-to-workers',
      d: 'M208,384 L252,384 A20,20 0 0,1 264,404 L264,448', // From EC2 Platform (bottom) to Workers (left)
      gradientId: 'ec2-workers-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'ec2-platform-to-redis',
      d: 'M208,376 L364,376 A20,20 0 0,1 384,396 L384,448', // From EC2 Platform (bottom) to Workers (left)
      gradientId: 'ec2-redis-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    },
    {
      id: 'workers-to-redis',
      d: 'M280,448 L280,404 A20,20 0 0,1 300,384 L356,384 A20,20 0 0,1 376,404 L376,448', // From Workers (right) to Redis (left)
      gradientId: 'workers-redis-gradient',
      startColor: '#11EFE3',
      endColor: '#9966FF'
    }
  ], []);
  const connections = staticConnections;

  // Animation state
  const [animatedPaths, setAnimatedPaths] = useState(new Set());
  const [unwindingPaths, setUnwindingPaths] = useState(new Set());
  const [pathLengths, setPathLengths] = useState({});
  const svgRef = useRef(null);

  // Calculate path lengths on mount
  useEffect(() => {
    if (svgRef.current) {
      const lengths = {};
      staticConnections.forEach(conn => {
        try {
          const pathElement = svgRef.current.querySelector(`[data-path-id="${conn.id}"]`);
          if (pathElement) {
            const length = pathElement.getTotalLength();
            if (length > 0) {
              lengths[conn.id] = length;
            }
          }
        } catch (error) {
          console.warn(`Error calculating length for path ${conn.id}:`, error);
        }
      });
      setPathLengths(lengths);
    }
  }, [staticConnections]);

  // Auto-animate paths on mount
  useEffect(() => {
    if (Object.keys(pathLengths).length > 0) {
      let isActive = true;
      let timeoutId;
      
      const animateSequence = async () => {
        if (!isActive) return;
        
        // Reset all states first
        setAnimatedPaths(new Set());
        setUnwindingPaths(new Set());
        
        // Wait a bit for reset to take effect
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (!isActive) return;
        
        // Start with all paths hidden by setting strokeDashoffset to pathLength
        for (const conn of staticConnections) {
          if (!isActive) return;
          try {
            const pathElement = svgRef.current?.querySelector(`[data-path-id="${conn.id}"]`);
            if (pathElement && pathLengths[conn.id]) {
              pathElement.style.strokeDashoffset = pathLengths[conn.id];
            }
          } catch (error) {
            console.warn(`Error setting initial state for path ${conn.id}:`, error);
          }
        }
        
        // Wait for initial hidden state to be set
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (!isActive) return;
        
        // Animate each path in sequence (0% to 100%)
        for (const conn of staticConnections) {
          if (!isActive) return;
          setAnimatedPaths(prev => new Set([...prev, conn.id]));
          await new Promise(resolve => setTimeout(resolve, 400));
        }
        
        if (!isActive) return;
        
        // Wait for all animations to complete
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (!isActive) return;
        
        // Start unwinding animation - erase from start to end
        for (const conn of staticConnections) {
          if (!isActive) return;
          setUnwindingPaths(prev => new Set([...prev, conn.id]));
          await new Promise(resolve => setTimeout(resolve, 400));
        }
        
        if (!isActive) return;
        
        // Wait for unwinding to complete
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (!isActive) return;
        
        // Restart the sequence after a pause
        timeoutId = setTimeout(() => {
          if (isActive) {
            animateSequence();
          }
        }, 1000);
      };
      
      animateSequence();
      
      // Cleanup function
      return () => {
        isActive = false;
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        setAnimatedPaths(new Set());
        setUnwindingPaths(new Set());
      };
    }
  }, [pathLengths, staticConnections]);

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
          <div className="relative bg-transparent rounded-xl">
            {/* Grid Container */}
            <div 
              className="w-[432px] h-[544px] relative"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gridTemplateRows: 'repeat(5, 1fr)',
                gap: '16px'
              }}
            >
              {/* Animated Connection Lines */}
              <svg
                ref={svgRef}
                width="100%" 
                height="100%"
                className="absolute inset-0 pointer-events-none"
                style={{ zIndex: 1 }}
                viewBox="0 0 432 544"
              >
                <defs>
                  {connections.map((conn) => (
                    <linearGradient
                      key={conn.gradientId}
                      id={conn.gradientId}
                      gradientUnits="userSpaceOnUse"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="100%"
                    >
                      <stop offset="0%" stopColor={conn.startColor} />
                      <stop offset="100%" stopColor={conn.endColor} />
                    </linearGradient>
                  ))}
                </defs>
                
                {connections.map((conn, index) => (
                  <path
                    key={conn.id || index}
                    data-path-id={conn.id}
                    d={conn.d}
                    stroke={`url(#${conn.gradientId})`}
                    strokeWidth="2"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                                         className={(animatedPaths.has(conn.id) || unwindingPaths.has(conn.id)) ? 'animated-path' : ''}
                     style={{
                       '--path-length': pathLengths[conn.id] || 0,
                       strokeDasharray: `${pathLengths[conn.id] || 0} ${pathLengths[conn.id] || 0}`,
                       strokeDashoffset: unwindingPaths.has(conn.id) ? -(pathLengths[conn.id] || 0) : (animatedPaths.has(conn.id) ? 0 : (pathLengths[conn.id] || 0)),
                       opacity: 1,
                       transition: (animatedPaths.has(conn.id) || unwindingPaths.has(conn.id)) ? 'stroke-dashoffset 2s ease-out' : 'none'
                     }}
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
