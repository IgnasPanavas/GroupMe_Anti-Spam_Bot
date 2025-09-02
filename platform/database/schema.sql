-- SpamShield Platform Database Schema
-- PostgreSQL Schema for robust multi-group spam monitoring

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Groups table - stores information about monitored GroupMe groups
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'error')),
    owner_id VARCHAR(50),
    owner_name VARCHAR(255),
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checked TIMESTAMP WITH TIME ZONE,
    last_message_id VARCHAR(50),
    error_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for groups table
CREATE INDEX idx_groups_group_id ON groups(group_id);
CREATE INDEX idx_groups_status ON groups(status);
CREATE INDEX idx_groups_updated_at ON groups(updated_at);

-- Group configurations - per-group settings and thresholds
CREATE TABLE group_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) REFERENCES groups(group_id) ON DELETE CASCADE,
    
    -- Spam detection settings
    confidence_threshold DECIMAL(3,2) DEFAULT 0.80 CHECK (confidence_threshold BETWEEN 0.0 AND 1.0),
    check_interval_seconds INTEGER DEFAULT 30 CHECK (check_interval_seconds BETWEEN 5 AND 3600),
    
    -- Action settings
    auto_delete_spam BOOLEAN DEFAULT true,
    notify_on_removal BOOLEAN DEFAULT true,
    notify_admins BOOLEAN DEFAULT true,
    send_startup_message BOOLEAN DEFAULT true,
    
    -- Advanced settings
    max_message_age_hours INTEGER DEFAULT 24,
    batch_size INTEGER DEFAULT 20,
    rate_limit_per_minute INTEGER DEFAULT 60,
    
    -- Model settings
    model_version VARCHAR(50) DEFAULT 'latest',
    custom_keywords TEXT[], -- Array of custom spam keywords
    whitelist_users TEXT[], -- Array of user IDs to never flag
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(group_id)
);

-- Bot instances - tracks running bot instances and their assignments
CREATE TABLE bot_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_name VARCHAR(100) NOT NULL,
    hostname VARCHAR(255),
    process_id INTEGER,
    status VARCHAR(20) DEFAULT 'starting' CHECK (status IN ('starting', 'running', 'stopping', 'stopped', 'error')),
    
    -- Capacity and load
    max_groups INTEGER DEFAULT 10,
    current_groups INTEGER DEFAULT 0,
    cpu_usage DECIMAL(5,2),
    memory_usage_mb INTEGER,
    
    -- Health tracking
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version VARCHAR(20),
    
    -- Assigned groups
    assigned_groups TEXT[], -- Array of group IDs
    
    UNIQUE(instance_name)
);

-- Group assignments - which bot instance monitors which group
CREATE TABLE group_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) REFERENCES groups(group_id) ON DELETE CASCADE,
    instance_id UUID REFERENCES bot_instances(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'reassigning')),
    
    UNIQUE(group_id, instance_id)
);

-- Message processing logs - tracks all processed messages
CREATE TABLE message_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) NOT NULL,
    message_id VARCHAR(50) NOT NULL,
    sender_id VARCHAR(50),
    sender_name VARCHAR(255),
    message_text TEXT,
    has_attachments BOOLEAN DEFAULT false,
    attachment_types TEXT[],
    
    -- Spam detection results
    is_spam BOOLEAN,
    confidence_score DECIMAL(5,4),
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    
    -- Actions taken
    action_taken VARCHAR(50), -- 'deleted', 'flagged', 'ignored', 'whitelisted'
    deletion_successful BOOLEAN,
    notification_sent BOOLEAN,
    
    -- Timestamps
    message_created_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for message_logs table
CREATE INDEX idx_message_logs_group_id ON message_logs(group_id);
CREATE INDEX idx_message_logs_processed_at ON message_logs(processed_at);
CREATE INDEX idx_message_logs_is_spam ON message_logs(is_spam);
CREATE INDEX idx_message_logs_message_id ON message_logs(message_id);

-- Daily statistics - aggregated metrics per group per day
CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    
    -- Message counts
    total_messages INTEGER DEFAULT 0,
    spam_detected INTEGER DEFAULT 0,
    spam_deleted INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0, -- manually reported
    
    -- Performance metrics
    avg_confidence_score DECIMAL(5,4),
    avg_processing_time_ms INTEGER,
    total_processing_time_ms BIGINT DEFAULT 0,
    
    -- Error tracking
    api_errors INTEGER DEFAULT 0,
    deletion_failures INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(group_id, date)
);

-- Create indexes for daily_stats table
CREATE INDEX idx_daily_stats_group_date ON daily_stats(group_id, date);
CREATE INDEX idx_daily_stats_date ON daily_stats(date);

-- Model versions - tracks different ML model versions and their performance
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) UNIQUE NOT NULL,
    model_file_path VARCHAR(500) NOT NULL,
    vectorizer_file_path VARCHAR(500) NOT NULL,
    
    -- Performance metrics
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    
    -- Training info
    training_data_size INTEGER,
    training_date TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for model_versions table
CREATE INDEX idx_model_versions_version ON model_versions(version);
CREATE INDEX idx_model_versions_active ON model_versions(is_active);

-- System events - audit log for platform operations
CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL, -- 'group_added', 'config_changed', 'instance_started', etc.
    entity_type VARCHAR(50), -- 'group', 'instance', 'config', 'model'
    entity_id VARCHAR(100),
    
    -- Event details
    description TEXT,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    
    -- Context
    user_id VARCHAR(50),
    instance_name VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for system_events table
CREATE INDEX idx_system_events_type ON system_events(event_type);
CREATE INDEX idx_system_events_created_at ON system_events(created_at);
CREATE INDEX idx_system_events_severity ON system_events(severity);

-- Configuration cache - for hot-reloading configuration
CREATE TABLE config_cache (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User management (for admin dashboard)
CREATE TABLE platform_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Permissions
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('admin', 'operator', 'viewer')),
    permissions JSONB DEFAULT '{}',
    
    -- Profile
    full_name VARCHAR(255),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_group_configs_updated_at BEFORE UPDATE ON group_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_stats_updated_at BEFORE UPDATE ON daily_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_config_cache_updated_at BEFORE UPDATE ON config_cache FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_platform_users_updated_at BEFORE UPDATE ON platform_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default model version
INSERT INTO model_versions (version, model_file_path, vectorizer_file_path, accuracy, is_active, is_default, created_by)
VALUES ('1.0.0', 'data/training/spam_detection_model.pkl', 'data/training/tfidf_vectorizer.pkl', 0.975, true, true, 'system');

-- Insert default admin user (password: 'admin123' - change this!)
INSERT INTO platform_users (username, email, password_hash, role, full_name)
VALUES ('admin', 'admin@spamshield.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VcXPWlXUa', 'admin', 'System Administrator');
