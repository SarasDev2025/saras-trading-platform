/**
 * Simple Broker Selection Test
 * Tests broker selection functionality by trying to create a small investment
 */

const API_BASE_URL = 'http://localhost:8000';

// US-based test user for Alpaca broker selection
const testUser = {
    email: 'john.doe@example.com',
    password: 'password123',
    investmentAmount: 250000  // Above minimum threshold
};

// Test state tracking
let testState = {
    authToken: null,
    investmentId: null,
    smallcaseId: null
};

async function authenticate() {
    console.log('🔐 Authenticating user...');
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
    console.log('✅ Authentication successful');
    return testState.authToken;
}

async function getSmallcases() {
    console.log('📦 Fetching smallcases...');
    const response = await fetch(`${API_BASE_URL}/smallcases/`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch smallcases: ${response.status}`);
    }

    const data = await response.json();
    console.log(`📊 Found ${data.data.length} total smallcases`);

    // Show all smallcases and their investment status
    data.data.forEach((sc, index) => {
        console.log(`   ${index + 1}. ${sc.name} - Invested: ${sc.isInvested ? 'Yes' : 'No'}`);
    });

    const availableSmallcases = data.data.filter(sc => !sc.isInvested);
    if (availableSmallcases.length === 0) {
        throw new Error('No available smallcases for testing');
    }

    return availableSmallcases[0]; // Return first available
}

async function testCreateInvestment(smallcase) {
    console.log(`🎯 Testing investment creation for: ${smallcase.name}`);

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
        console.log(`❌ Investment failed: ${errorData.detail || response.status}`);
        return null;
    }

    const data = await response.json();
    testState.investmentId = data.data.investmentId;
    testState.smallcaseId = smallcase.id;
    console.log(`✅ Investment created: ${testState.investmentId}`);
    return data.data;
}

async function checkBrokerConnection() {
    console.log('🔗 Checking broker connection...');

    const response = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
        headers: { 'Authorization': `Bearer ${testState.authToken}` }
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch user investments: ${response.status}`);
    }

    const data = await response.json();
    const investment = data.data.find(inv => inv.id === testState.investmentId);

    if (!investment) {
        console.log('❌ Investment not found');
        return null;
    }

    console.log('📋 Investment details:');
    console.log(`   Investment ID: ${investment.id}`);
    console.log(`   Status: ${investment.status}`);
    console.log(`   Amount: $${investment.investment_amount}`);

    if (investment.broker_connection) {
        console.log('🏦 Broker Connection:');
        console.log(`   Broker Type: ${investment.broker_connection.broker_type}`);
        console.log(`   Connection ID: ${investment.broker_connection.id}`);
        console.log(`   Alias: ${investment.broker_connection.alias}`);
        console.log(`   Status: ${investment.broker_connection.status}`);

        // Check if Alpaca was selected
        if (investment.broker_connection.broker_type === 'alpaca') {
            console.log('✅ Alpaca broker correctly selected for US user');
            return true;
        } else {
            console.log(`⚠️  Unexpected broker selected: ${investment.broker_connection.broker_type}`);
            return false;
        }
    } else {
        console.log('❌ No broker connection found');
        return false;
    }
}

async function runBrokerSelectionTest() {
    console.log('🚀 Starting Broker Selection Test');
    console.log('='.repeat(50));

    try {
        // Step 1: Authentication
        await authenticate();

        // Step 2: Get smallcases
        const smallcase = await getSmallcases();
        console.log(`✅ Selected smallcase: ${smallcase.name}`);

        // Step 3: Test investment creation (broker selection happens here)
        const investment = await testCreateInvestment(smallcase);
        if (!investment) {
            console.log('💥 Test failed: Could not create investment');
            return;
        }

        // Wait a moment for processing
        console.log('⏳ Waiting for broker selection processing...');
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Step 4: Check broker connection
        const brokerOk = await checkBrokerConnection();

        if (brokerOk) {
            console.log('\n🎉 BROKER SELECTION TEST PASSED! 🎉');
            console.log('✅ Alpaca broker was correctly selected for US user');
        } else {
            console.log('\n💥 BROKER SELECTION TEST FAILED');
            console.log('❌ Alpaca broker was not selected as expected');
        }

    } catch (error) {
        console.log(`💥 Test failed: ${error.message}`);
        if (error.stack) {
            console.log('\n📚 Stack trace:');
            console.log(error.stack);
        }
    }
}

// Run the test
runBrokerSelectionTest().catch(console.error);