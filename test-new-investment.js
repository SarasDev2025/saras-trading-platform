/**
 * Test script to create a new investment and verify holdings are properly created
 */

const API_BASE_URL = 'http://localhost:8000';

async function getAuthToken() {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'username=john.doe@example.com&password=password123'
    });

    if (!response.ok) {
        throw new Error('Failed to authenticate');
    }

    const data = await response.json();
    return data.access_token || data.data?.access_token;
}

async function testNewInvestment() {
    console.log('🚀 Testing New Investment Creation & Holdings\n');

    try {
        // Step 1: Get auth token
        console.log('1. Getting authentication token...');
        const token = await getAuthToken();
        console.log('✅ Authentication successful');

        // Step 2: Get available smallcases
        console.log('\n2. Fetching available smallcases...');
        const smallcasesResponse = await fetch(`${API_BASE_URL}/smallcases/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!smallcasesResponse.ok) {
            throw new Error('Failed to fetch smallcases');
        }

        const smallcasesData = await smallcasesResponse.json();
        const availableSmallcases = smallcasesData.data.filter(sc => !sc.isInvested);

        console.log(`✅ Found ${availableSmallcases.length} available smallcases`);

        if (availableSmallcases.length === 0) {
            console.log('❌ No available smallcases for investment');
            return;
        }

        // Pick the first available smallcase
        const testSmallcase = availableSmallcases[0];
        console.log(`📊 Selected smallcase: ${testSmallcase.name} (${testSmallcase.id})`);
        console.log(`💰 Minimum investment: $${testSmallcase.minimumInvestment}`);

        // Step 3: Create new investment
        console.log('\n3. Creating new investment...');
        const investmentAmount = Math.max(testSmallcase.minimumInvestment, 5000);

        const investResponse = await fetch(`${API_BASE_URL}/smallcases/${testSmallcase.id}/invest`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: investmentAmount,
                execution_mode: 'paper'
            })
        });

        if (!investResponse.ok) {
            const errorData = await investResponse.json();
            console.error('❌ Investment failed:', errorData);
            return;
        }

        const investData = await investResponse.json();
        console.log('✅ Investment created successfully');
        console.log(`💵 Investment amount: $${investmentAmount}`);

        // Wait a moment for processing
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Step 4: Get the new investment details
        console.log('\n4. Fetching investment details...');
        const investmentsResponse = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const investmentsData = await investmentsResponse.json();
        const newInvestment = investmentsData.data.find(inv =>
            inv.smallcase.id === testSmallcase.id && inv.status === 'active'
        );

        if (!newInvestment) {
            console.error('❌ Could not find the new investment');
            return;
        }

        console.log('✅ Found new investment:');
        console.log(`   ID: ${newInvestment.id}`);
        console.log(`   Amount: $${newInvestment.investmentAmount}`);
        console.log(`   Current Value: $${newInvestment.currentValue}`);
        console.log(`   Status: ${newInvestment.status}`);

        // Step 5: Test closure preview (this will tell us if holdings exist)
        console.log('\n5. Testing closure preview to check holdings...');
        const previewResponse = await fetch(
            `${API_BASE_URL}/smallcases/investments/${newInvestment.id}/closure-preview`,
            {
                headers: { 'Authorization': `Bearer ${token}` }
            }
        );

        if (!previewResponse.ok) {
            const errorData = await previewResponse.json();
            console.error('❌ Closure preview failed:', errorData);

            if (errorData.detail.includes('No holdings found')) {
                console.log('🔍 ISSUE IDENTIFIED: Holdings are not being created during investment!');
                console.log('📝 This means the investment creation process needs to be fixed.');

                // Let's check what the investment creation endpoint actually does
                console.log('\n6. Investigating investment creation process...');
                console.log('   The issue is likely in the smallcase investment endpoint');
                console.log('   It creates the investment record but not the underlying portfolio holdings');

                return { issue: 'no_holdings_created', investment: newInvestment };
            }
        } else {
            const previewData = await previewResponse.json();
            console.log('✅ Closure preview successful - holdings exist!');
            console.log(`💰 Current value: $${previewData.data.current_value}`);
            console.log(`📊 Holdings found: ${previewData.data.holdings_to_close?.length || 'unknown'}`);

            // Step 6: Test actual closure
            console.log('\n6. Testing actual closure...');
            const closeResponse = await fetch(
                `${API_BASE_URL}/smallcases/investments/${newInvestment.id}/close`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        closure_reason: 'test_new_investment'
                    })
                }
            );

            if (!closeResponse.ok) {
                const errorData = await closeResponse.json();
                console.error('❌ Closure failed:', errorData);
            } else {
                const closeData = await closeResponse.json();
                console.log('✅ Closure successful!');
                console.log(`💰 Exit value: $${closeData.data.exit_value}`);
                console.log(`📈 Realized P&L: $${closeData.data.realized_pnl}`);
            }

            return { success: true, investment: newInvestment };
        }

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { error: error.message };
    }
}

// Run the test
testNewInvestment()
    .then(result => {
        console.log('\n' + '='.repeat(50));
        if (result?.issue === 'no_holdings_created') {
            console.log('🎯 CONCLUSION: Investment creation is missing portfolio holdings creation');
            console.log('📋 Next steps:');
            console.log('   1. Fix the investment endpoint to create actual portfolio holdings');
            console.log('   2. This involves creating entries in portfolio_holdings table');
            console.log('   3. Holdings should be based on smallcase constituents and investment amount');
        } else if (result?.success) {
            console.log('🎉 SUCCESS: Investment and closure flow working correctly!');
        } else {
            console.log('❓ Unexpected result:', result);
        }
    })
    .catch(console.error);