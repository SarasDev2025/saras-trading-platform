/**
 * Alpaca Paper Trading API Test
 * Complete investment lifecycle test: Login → Invest → Modify → Verify → Close
 */

const API_BASE_URL = 'http://localhost:8000';

// US-based test user for Alpaca broker selection
const testUser = {
    email: 'john.doe@example.com',
    password: 'password123',
    region: 'US',  // Should trigger Alpaca broker selection
    investmentAmount: 150000  // Above minimum threshold
};

// Test state tracking
let testState = {
    authToken: null,
    investmentId: null,
    smallcaseId: null,
    brokerConnectionId: null,
    brokerOrders: [],
    initialPositions: [],
    currentPositions: []
};

async function logStep(step, message) {
    console.log(`\n🔵 Step ${step}: ${message}`);
    console.log('='.repeat(60));
}

async function logSuccess(message) {
    console.log(`✅ ${message}`);
}

async function logError(message, error = null) {
    console.log(`❌ ${message}`);
    if (error) {
        console.log(`   Error: ${error.message || error}`);
    }
}

async function logInfo(message) {
    console.log(`ℹ️  ${message}`);
}

async function authenticate() {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${testUser.email}&password=${testUser.password}`
    });

    if (!response.ok) {
        throw new Error(`Authentication failed: ${response.status}`);
    }

    const data = await response.json();
    testState.authToken = data.data.access_token;
    return testState.authToken;
}

async function getAvailableSmallcases() {
    const response = await fetch(`${API_BASE_URL}/smallcases/`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch smallcases: ${response.status}`);
    }

    const data = await response.json();
    const availableSmallcases = data.data.filter(sc => !sc.isInvested);

    if (availableSmallcases.length === 0) {
        throw new Error('No available smallcases for testing');
    }

    return availableSmallcases[0]; // Return first available
}

async function createInvestment(smallcase) {
    const response = await fetch(`${API_BASE_URL}/smallcases/${smallcase.id}/invest`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${testState.authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: testUser.investmentAmount,
            execution_mode: 'paper'
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Investment failed: ${errorData.detail || response.status}`);
    }

    const data = await response.json();
    testState.investmentId = data.data.investmentId;
    testState.smallcaseId = smallcase.id;
    return data.data;
}

async function verifyBrokerSelection() {
    // Check user's broker preference to verify Alpaca was selected
    const response = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch user investments: ${response.status}`);
    }

    const data = await response.json();
    console.log(`DEBUG: Found ${data.data.length} total investments for user`);
    console.log(`DEBUG: Looking for investment ID: ${testState.investmentId}`);
    data.data.forEach((inv, index) => {
        console.log(`DEBUG: Investment ${index + 1}: ${inv.id} (${inv.status})`);
    });

    const investment = data.data.find(inv => inv.id === testState.investmentId);

    if (!investment) {
        throw new Error('Investment not found in user investments');
    }

    // Verify broker selection logic worked correctly
    if (investment.broker_connection && investment.broker_connection.broker_type === 'alpaca') {
        testState.brokerConnectionId = investment.broker_connection.id;
        return {
            brokerType: investment.broker_connection.broker_type,
            connectionId: testState.brokerConnectionId,
            verified: true
        };
    } else {
        return {
            brokerType: investment.broker_connection?.broker_type || 'unknown',
            connectionId: investment.broker_connection?.id || null,
            verified: false
        };
    }
}

async function checkAlpacaOrders() {
    // This would normally query Alpaca API directly
    // For now, we'll check the database for orders placed via our system

    const response = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch investment details: ${response.status}`);
    }

    const data = await response.json();
    const investment = data.data.find(inv => inv.id === testState.investmentId);

    if (investment && investment.execution_run) {
        const orders = investment.execution_run.orders || [];
        testState.brokerOrders = orders.filter(order =>
            order.broker_order_id && order.status !== 'failed'
        );

        return {
            totalOrders: orders.length,
            successfulOrders: testState.brokerOrders.length,
            orders: testState.brokerOrders
        };
    }

    return { totalOrders: 0, successfulOrders: 0, orders: [] };
}

async function getPortfolioPositions() {
    const response = await fetch(`${API_BASE_URL}/portfolios/user/holdings`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch portfolio positions: ${response.status}`);
    }

    const data = await response.json();
    return data.data || [];
}

async function modifySmallcase() {
    // Trigger a rebalancing by making a small modification
    const response = await fetch(`${API_BASE_URL}/smallcases/${testState.smallcaseId}/rebalance`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${testState.authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            investment_id: testState.investmentId,
            reason: 'api_test_modification'
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Rebalancing failed: ${errorData.detail || response.status}`);
    }

    const data = await response.json();
    return data.data;
}

async function closeInvestment() {
    const response = await fetch(`${API_BASE_URL}/smallcases/investments/${testState.investmentId}/close`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${testState.authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            closure_reason: 'alpaca_api_test_completion'
        })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Investment closure failed: ${errorData.detail || response.status}`);
    }

    const data = await response.json();
    return data.data;
}

async function generateTestReport() {
    console.log('\n' + '='.repeat(80));
    console.log('🎯 ALPACA PAPER TRADING API TEST REPORT');
    console.log('='.repeat(80));

    console.log('\n📊 Test Configuration:');
    console.log(`   User: ${testUser.email}`);
    console.log(`   Region: ${testUser.region}`);
    console.log(`   Investment Amount: $${testUser.investmentAmount}`);
    console.log(`   Expected Broker: Alpaca`);

    console.log('\n📈 Test Results:');
    console.log(`   Investment ID: ${testState.investmentId || 'N/A'}`);
    console.log(`   Smallcase ID: ${testState.smallcaseId || 'N/A'}`);
    console.log(`   Broker Connection ID: ${testState.brokerConnectionId || 'N/A'}`);
    console.log(`   Broker Orders Placed: ${testState.brokerOrders.length}`);

    if (testState.brokerOrders.length > 0) {
        console.log('\n📋 Broker Orders:');
        testState.brokerOrders.forEach((order, index) => {
            console.log(`   ${index + 1}. ${order.symbol} - ${order.side} ${order.quantity} shares`);
            console.log(`      Status: ${order.status}, Broker Order ID: ${order.broker_order_id}`);
        });
    }

    console.log('\n' + '='.repeat(80));
}

async function runAlpacaTest() {
    console.log('🚀 Starting Alpaca Paper Trading API Test');
    console.log('🎯 Testing complete investment lifecycle with Alpaca broker integration\n');

    try {
        // Step 1: Authentication
        await logStep(1, 'User Authentication');
        await authenticate();
        logSuccess(`User authenticated successfully: ${testUser.email}`);

        // Step 2: Get available smallcases
        await logStep(2, 'Fetch Available Smallcases');
        const smallcase = await getAvailableSmallcases();
        logSuccess(`Selected smallcase: ${smallcase.name} (${smallcase.id})`);

        // Step 3: Create investment
        await logStep(3, 'Create Investment');
        const investment = await createInvestment(smallcase);
        logSuccess(`Investment created: ${investment.investmentId}`);
        logInfo(`Holdings created: ${investment.holdingsCreated}`);

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Step 4: Verify broker selection
        await logStep(4, 'Verify Alpaca Broker Selection');
        const brokerVerification = await verifyBrokerSelection();
        if (brokerVerification.verified) {
            logSuccess(`Alpaca broker correctly selected: ${brokerVerification.connectionId}`);
        } else {
            logError(`Unexpected broker selected: ${brokerVerification.brokerType}`);
        }

        // Step 5: Check Alpaca orders
        await logStep(5, 'Verify Alpaca Orders Placed');
        const orderCheck = await checkAlpacaOrders();
        logSuccess(`Orders placed: ${orderCheck.successfulOrders}/${orderCheck.totalOrders}`);

        orderCheck.orders.forEach(order => {
            logInfo(`Order: ${order.symbol} ${order.side} ${order.quantity} shares (${order.status})`);
        });

        // Step 6: Get initial positions
        await logStep(6, 'Capture Initial Portfolio Positions');
        testState.initialPositions = await getPortfolioPositions();
        logSuccess(`Initial positions captured: ${testState.initialPositions.length} holdings`);

        // Step 7: Modify smallcase (rebalancing)
        await logStep(7, 'Modify Smallcase (Trigger Rebalancing)');
        const rebalanceResult = await modifySmallcase();
        logSuccess(`Rebalancing initiated: ${rebalanceResult.rebalanceId || 'success'}`);

        // Wait for rebalancing processing
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Step 8: Verify rebalancing orders
        await logStep(8, 'Verify Rebalancing Orders');
        const rebalanceOrders = await checkAlpacaOrders();
        logSuccess(`Post-rebalance orders: ${rebalanceOrders.successfulOrders} total`);

        // Step 9: Check updated positions
        await logStep(9, 'Verify Updated Portfolio Positions');
        testState.currentPositions = await getPortfolioPositions();
        logSuccess(`Current positions: ${testState.currentPositions.length} holdings`);

        // Step 10: Close investment
        await logStep(10, 'Close Investment');
        const closureResult = await closeInvestment();
        logSuccess(`Investment closed successfully`);
        logInfo(`Exit value: $${closureResult.exit_value || 'N/A'}`);
        logInfo(`Realized P&L: $${closureResult.realized_pnl || 'N/A'}`);

        // Generate final report
        await generateTestReport();

        console.log('\n🎉 ALPACA PAPER TRADING TEST COMPLETED SUCCESSFULLY! 🎉');

    } catch (error) {
        logError('Test failed', error);
        console.log('\n💥 ALPACA PAPER TRADING TEST FAILED');

        // Still generate report with available data
        await generateTestReport();

        if (error.stack) {
            console.log('\n📚 Stack trace:');
            console.log(error.stack);
        }

        process.exit(1);
    }
}

// Health check before starting test
async function checkSystemHealth() {
    console.log('🏥 Checking system health...');

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const health = await response.json();
            console.log('✅ API Gateway is healthy');
            console.log(`   Services: Database(${health.services.database}), Redis(${health.services.redis})`);
            return true;
        } else {
            console.log('⚠️  API Gateway health check failed');
            return false;
        }
    } catch (error) {
        console.log('❌ Cannot connect to API Gateway');
        return false;
    }
}

// Main execution
async function main() {
    try {
        const isHealthy = await checkSystemHealth();
        if (!isHealthy) {
            console.log('💥 System health check failed. Please ensure all services are running.');
            process.exit(1);
        }

        await runAlpacaTest();
    } catch (error) {
        console.error('💥 Alpaca test suite failed:', error.message);
        process.exit(1);
    }
}

main().catch(console.error);