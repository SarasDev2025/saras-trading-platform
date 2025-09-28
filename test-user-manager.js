/**
 * Test User Management Utilities
 * Handles creation, cleanup, and management of test users for broker API testing
 */

const API_BASE_URL = 'http://localhost:8000';

// Test user configurations for different brokers
const TEST_USERS = {
    alpaca: {
        username: 'johndoe',
        email: 'john.doe@example.com',
        password: 'Password123',
        first_name: 'John',
        last_name: 'Doe',
        region: 'US',
        phone: '+1-555-0123',
        date_of_birth: '1990-01-15',
        investment_experience: 'intermediate',
        risk_tolerance: 'moderate'
    },
    zerodha: {
        username: 'priyasharma',
        email: 'priya.sharma@example.com',
        password: 'Password123',
        first_name: 'Priya',
        last_name: 'Sharma',
        region: 'IN',
        phone: '+91-9876543210',
        date_of_birth: '1992-06-20',
        investment_experience: 'beginner',
        risk_tolerance: 'conservative'
    }
};

class TestUserManager {
    constructor() {
        this.createdUsers = [];
        this.authTokens = {};
    }

    async logInfo(message) {
        console.log(`ℹ️  ${message}`);
    }

    async logSuccess(message) {
        console.log(`✅ ${message}`);
    }

    async logError(message, error = null) {
        console.log(`❌ ${message}`);
        if (error) {
            console.log(`   Error: ${error.message || error}`);
        }
    }

    async logWarning(message) {
        console.log(`⚠️  ${message}`);
    }

    /**
     * Check if API Gateway is healthy
     */
    async checkSystemHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                const health = await response.json();
                this.logSuccess('API Gateway is healthy');
                this.logInfo(`Services: Database(${health.services.database}), Redis(${health.services.redis})`);
                return true;
            } else {
                this.logWarning('API Gateway health check failed');
                return false;
            }
        } catch (error) {
            this.logError('Cannot connect to API Gateway', error);
            return false;
        }
    }

    /**
     * Create a test user for specific broker
     */
    async createTestUser(brokerType) {
        if (!TEST_USERS[brokerType]) {
            throw new Error(`Unknown broker type: ${brokerType}`);
        }

        const userData = TEST_USERS[brokerType];

        try {
            // Check if user already exists
            const existingUser = await this.checkUserExists(userData.email);
            if (existingUser) {
                this.logInfo(`Test user ${userData.email} already exists - using existing user`);

                // Add to created users list for tracking
                this.createdUsers.push({
                    broker: brokerType,
                    email: userData.email,
                    userId: existingUser.user_id,
                    region: userData.region,
                    existed: true
                });

                return existingUser;
            }

            // Create new user
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const errorData = await response.json();

                // Check if error is due to existing user (common error case)
                if (errorData.detail && (
                    errorData.detail.includes('already exists') ||
                    errorData.detail.includes('duplicate') ||
                    errorData.detail.includes('unique constraint') ||
                    response.status === 409
                )) {
                    this.logWarning(`User ${userData.email} exists but login check missed it - attempting login`);

                    // Try to authenticate with existing user
                    const existingUserRetry = await this.checkUserExists(userData.email);
                    if (existingUserRetry) {
                        this.logInfo(`Successfully found existing user: ${userData.email}`);
                        this.createdUsers.push({
                            broker: brokerType,
                            email: userData.email,
                            userId: existingUserRetry.user_id,
                            region: userData.region,
                            existed: true
                        });
                        return existingUserRetry;
                    }
                }

                const errorMsg = errorData.detail || errorData.message || JSON.stringify(errorData) || response.status;
                throw new Error(`User creation failed: ${errorMsg}`);
            }

            const result = await response.json();
            this.createdUsers.push({
                broker: brokerType,
                email: userData.email,
                userId: result.data.user_id,
                region: userData.region,
                existed: false
            });

            this.logSuccess(`Created new test user: ${userData.email} for ${brokerType} broker`);
            return result.data;

        } catch (error) {
            // Last resort: try to use existing user if creation fails
            if (error.message.includes('already exists') || error.message.includes('duplicate')) {
                this.logWarning(`Registration failed but user might exist - attempting final login check`);
                const finalCheck = await this.checkUserExists(userData.email);
                if (finalCheck) {
                    this.logInfo(`Final check successful - using existing user: ${userData.email}`);
                    this.createdUsers.push({
                        broker: brokerType,
                        email: userData.email,
                        userId: finalCheck.user_id,
                        region: userData.region,
                        existed: true
                    });
                    return finalCheck;
                }
            }

            this.logError(`Failed to create or find test user for ${brokerType}`, error);
            throw error;
        }
    }

    /**
     * Check if user exists by attempting login
     */
    async checkUserExists(email) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${email}&password=Password123`
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    user_id: data.data.user_id,
                    email: email,
                    exists: true
                };
            }

            // Check if it's an authentication error (user exists but wrong password)
            // vs user not found error
            if (response.status === 401) {
                try {
                    const errorData = await response.json();
                    // If error indicates invalid credentials (not user not found),
                    // the user exists but password is wrong
                    if (errorData.detail &&
                        (errorData.detail.includes('Invalid credentials') ||
                         errorData.detail.includes('incorrect') ||
                         errorData.detail.includes('wrong password'))) {

                        this.logWarning(`User ${email} exists but password may have changed`);
                        return {
                            user_id: null,
                            email: email,
                            exists: true,
                            password_mismatch: true
                        };
                    }
                } catch (parseError) {
                    // If we can't parse the error, assume user doesn't exist
                }
            }

            return null;
        } catch (error) {
            // Network or other errors - assume user doesn't exist
            return null;
        }
    }

    /**
     * Authenticate test user and store token
     */
    async authenticateUser(brokerType) {
        const userData = TEST_USERS[brokerType];

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${userData.email}&password=${userData.password}`
            });

            if (!response.ok) {
                throw new Error(`Authentication failed for ${userData.email}: ${response.status}`);
            }

            const data = await response.json();
            this.authTokens[brokerType] = data.data.access_token;

            this.logSuccess(`Authenticated ${userData.email} for ${brokerType} testing`);
            return data.data.access_token;

        } catch (error) {
            this.logError(`Failed to authenticate user for ${brokerType}`, error);
            throw error;
        }
    }

    /**
     * Setup broker connection for test user
     */
    async setupBrokerConnection(brokerType) {
        const token = this.authTokens[brokerType];
        if (!token) {
            throw new Error(`No auth token available for ${brokerType}. Authenticate first.`);
        }

        try {
            // Check if broker connection already exists
            const existingConnections = await this.getBrokerConnections(brokerType);
            if (existingConnections.length > 0) {
                this.logInfo(`Broker connection already exists for ${brokerType}`);
                return existingConnections[0];
            }

            // Create broker connection
            const connectionData = {
                alias: `${brokerType}_test_connection`,
                broker_type: brokerType,
                api_key: `test_${brokerType}_key`,
                api_secret: `test_${brokerType}_secret`,
                paper_trading: true
            };

            const response = await fetch(`${API_BASE_URL}/brokers/connections`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(connectionData)
            });

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                } catch (parseError) {
                    errorMessage = `HTTP ${response.status} - ${response.statusText}`;
                }
                throw new Error(`Broker connection setup failed: ${errorMessage}`);
            }

            const result = await response.json();
            this.logSuccess(`Set up ${brokerType} broker connection`);
            return result.data;

        } catch (error) {
            const errorMessage = error.message || error.toString() || 'Unknown error';
            this.logError(`Failed to setup broker connection for ${brokerType}`, { message: errorMessage });
            throw new Error(`Broker connection setup failed: ${errorMessage}`);
        }
    }

    /**
     * Get existing broker connections for user
     */
    async getBrokerConnections(brokerType) {
        const token = this.authTokens[brokerType];

        try {
            const response = await fetch(`${API_BASE_URL}/brokers/connections`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                return [];
            }

            const data = await response.json();
            return data.data || [];

        } catch (error) {
            return [];
        }
    }

    /**
     * Clean up user investments and positions
     */
    async cleanupUserData(brokerType) {
        const token = this.authTokens[brokerType];
        if (!token) {
            this.logWarning(`No auth token for ${brokerType} cleanup`);
            return;
        }

        try {
            // Get user investments
            const investmentsResponse = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (investmentsResponse.ok) {
                const investmentsData = await investmentsResponse.json();
                const investments = investmentsData.data || [];

                // Close any open investments
                for (const investment of investments) {
                    if (investment.status === 'active') {
                        try {
                            await fetch(`${API_BASE_URL}/smallcases/investments/${investment.id}/close`, {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${token}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    closure_reason: 'test_cleanup'
                                })
                            });
                            this.logInfo(`Closed investment ${investment.id}`);
                        } catch (error) {
                            this.logWarning(`Failed to close investment ${investment.id}`);
                        }
                    }
                }
            }

            this.logSuccess(`Cleaned up user data for ${brokerType}`);

        } catch (error) {
            this.logError(`Failed to cleanup user data for ${brokerType}`, error);
        }
    }

    /**
     * Setup complete test environment for broker
     */
    async setupTestEnvironment(brokerType, skipBrokerConnection = false) {
        console.log(`\n🔧 Setting up test environment for ${brokerType.toUpperCase()}`);
        console.log('='.repeat(60));

        try {
            // Check system health
            const isHealthy = await this.checkSystemHealth();
            if (!isHealthy) {
                throw new Error('System health check failed');
            }

            // Create or verify test user
            await this.createTestUser(brokerType);

            // Authenticate user
            await this.authenticateUser(brokerType);

            // Setup broker connection (optional for testing)
            if (!skipBrokerConnection) {
                try {
                    await this.setupBrokerConnection(brokerType);
                } catch (error) {
                    this.logWarning(`Broker connection setup failed (using test credentials) - continuing without connection`);
                    this.logInfo(`Note: Tests will create broker connections dynamically as needed`);
                }
            } else {
                this.logInfo(`Skipping broker connection setup - will be created dynamically during tests`);
            }

            this.logSuccess(`Test environment ready for ${brokerType.toUpperCase()}`);
            return true;

        } catch (error) {
            this.logError(`Failed to setup test environment for ${brokerType}`, error);
            return false;
        }
    }

    /**
     * Cleanup test environment
     */
    async cleanupTestEnvironment() {
        console.log('\n🧹 Cleaning up test environment...');
        console.log('='.repeat(60));

        for (const brokerType of Object.keys(this.authTokens)) {
            await this.cleanupUserData(brokerType);
        }

        this.logSuccess('Test environment cleanup completed');
    }

    /**
     * Get test user credentials for broker
     */
    getTestUserCredentials(brokerType) {
        if (!TEST_USERS[brokerType]) {
            throw new Error(`Unknown broker type: ${brokerType}`);
        }
        return TEST_USERS[brokerType];
    }

    /**
     * Get auth token for broker
     */
    getAuthToken(brokerType) {
        return this.authTokens[brokerType];
    }

    /**
     * Display test environment status
     */
    async displayStatus() {
        console.log('\n📊 TEST ENVIRONMENT STATUS');
        console.log('='.repeat(60));

        for (const [brokerType, userData] of Object.entries(TEST_USERS)) {
            console.log(`\n${brokerType.toUpperCase()} Test User:`);
            console.log(`   Email: ${userData.email}`);
            console.log(`   Region: ${userData.region}`);
            console.log(`   Auth Token: ${this.authTokens[brokerType] ? '✅ Available' : '❌ Not set'}`);

            if (this.authTokens[brokerType]) {
                const connections = await this.getBrokerConnections(brokerType);
                console.log(`   Broker Connections: ${connections.length}`);
            }
        }

        console.log(`\nManaged Users: ${this.createdUsers.length}`);
        this.createdUsers.forEach(user => {
            const status = user.existed ? '🔄 Existing' : '🆕 Created';
            console.log(`   ${user.email} (${user.broker}) - ${user.region} - ${status}`);
        });
    }
}

// Export for use in test files
export { TestUserManager, TEST_USERS };

// CLI interface
async function main() {
    const manager = new TestUserManager();
    const args = process.argv.slice(2);
    const command = args[0];
    const brokerType = args[1];

    try {
        switch (command) {
            case 'setup':
                if (!brokerType || !['alpaca', 'zerodha'].includes(brokerType)) {
                    console.log('Usage: node test-user-manager.js setup <alpaca|zerodha> [--skip-broker]');
                    process.exit(1);
                }
                const skipBroker = args.includes('--skip-broker');
                await manager.setupTestEnvironment(brokerType, skipBroker);
                break;

            case 'cleanup':
                await manager.cleanupTestEnvironment();
                break;

            case 'status':
                await manager.displayStatus();
                break;

            case 'setup-all':
                const skipBrokerAll = args.includes('--skip-broker');
                await manager.setupTestEnvironment('alpaca', skipBrokerAll);
                await manager.setupTestEnvironment('zerodha', skipBrokerAll);
                break;

            default:
                console.log('\n📖 Test User Manager Usage:');
                console.log('='.repeat(40));
                console.log('node test-user-manager.js setup <alpaca|zerodha> [--skip-broker]  - Setup test user for specific broker');
                console.log('node test-user-manager.js setup-all [--skip-broker]              - Setup test users for all brokers');
                console.log('node test-user-manager.js cleanup                               - Cleanup all test data');
                console.log('node test-user-manager.js status                                - Show test environment status');
                console.log('\nExamples:');
                console.log('node test-user-manager.js setup alpaca --skip-broker');
                console.log('node test-user-manager.js setup-all --skip-broker');
                break;
        }
    } catch (error) {
        console.error('💥 Test user manager failed:', error.message);
        process.exit(1);
    }
}

// Run if called directly
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (process.argv[1] === __filename) {
    main().catch(console.error);
}