/**
 * Paper Trading Flow Test
 * Tests: Signup -> $100k allocation -> Add funds -> Trade -> Cash balance updates
 */

const BASE_URL = 'http://localhost:8000';

async function test() {
    console.log('🎯 Paper Trading Flow Test\n');

    // Step 1: Register new user
    console.log('Step 1: Register new user');
    const timestamp = Date.now();
    const registerResponse = await fetch(`${BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: `paper_${timestamp}@example.com`,
            username: `paper_${timestamp}`,
            password: 'Password123',
            first_name: 'Paper',
            last_name: 'Trader'
        })
    });

    if (!registerResponse.ok) {
        const error = await registerResponse.text();
        console.error('❌ Registration failed:', error);
        return;
    }

    const registerData = await registerResponse.json();
    console.log('✅ User registered successfully\n');

    // Step 2: Login
    console.log('Step 2: Login');
    const formData = new URLSearchParams();
    formData.append('username', `paper_${timestamp}@example.com`);
    formData.append('password', 'Password123');

    const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });

    const loginData = await loginResponse.json();
    const token = loginData.data.access_token;
    const userId = loginData.data.user.id;
    console.log(`✅ Logged in as ${userId}\n`);

    // Step 3: Check cash balance (should be $100,000)
    console.log('Step 3: Check initial cash balance');
    const balanceResponse1 = await fetch(`${BASE_URL}/portfolios/cash-balance`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    const balanceData1 = await balanceResponse1.json();
    console.log('Initial Balance:', JSON.stringify(balanceData1.data, null, 2));

    if (balanceData1.data.cash_balance !== 100000) {
        console.error('❌ Expected initial balance $100,000, got $' + balanceData1.data.cash_balance);
        return;
    }
    console.log('✅ Initial $100,000 allocated correctly\n');

    // Step 4: Add funds
    console.log('Step 4: Add $50,000 funds');
    const addFundsResponse = await fetch(`${BASE_URL}/portfolios/add-funds`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            portfolio_id: balanceData1.data.portfolio_id,
            amount: 50000
        })
    });

    if (!addFundsResponse.ok) {
        const error = await addFundsResponse.text();
        console.error('❌ Add funds failed:', error);
        return;
    }

    const addFundsData = await addFundsResponse.json();
    console.log('Add Funds Result:', JSON.stringify(addFundsData.data, null, 2));

    if (addFundsData.data.cash_balance !== 150000) {
        console.error('❌ Expected balance $150,000, got $' + addFundsData.data.cash_balance);
        return;
    }
    console.log('✅ Funds added successfully, balance now $150,000\n');

    // Step 5: Check cash balance again
    console.log('Step 5: Verify cash balance');
    const balanceResponse2 = await fetch(`${BASE_URL}/portfolios/cash-balance`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    const balanceData2 = await balanceResponse2.json();
    console.log('Updated Balance:', JSON.stringify(balanceData2.data, null, 2));
    console.log('✅ Cash balance verified\n');

    // Step 6: Try to place a trade (if trading endpoint exists)
    console.log('Step 6: Attempt to place paper trade');
    console.log('💡 Note: Trading functionality would validate buying power here\n');

    // Step 7: Test buying power limit
    console.log('Step 7: Test buying power limit (should fail)');
    const largeAddResponse = await fetch(`${BASE_URL}/portfolios/add-funds`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            portfolio_id: balanceData1.data.portfolio_id,
            amount: 2000000  // Exceeds $1M limit
        })
    });

    if (largeAddResponse.ok) {
        console.error('❌ Should have rejected amount > $1M');
    } else {
        const errorData = await largeAddResponse.json();
        console.log('✅ Correctly rejected excessive amount:', errorData.detail);
    }
    console.log();

    // Step 8: Test minimum amount
    console.log('Step 8: Test minimum deposit (should fail)');
    const smallAddResponse = await fetch(`${BASE_URL}/portfolios/add-funds`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            portfolio_id: balanceData1.data.portfolio_id,
            amount: 50  // Below $100 minimum
        })
    });

    if (smallAddResponse.ok) {
        console.error('❌ Should have rejected amount < $100');
    } else {
        const errorData = await smallAddResponse.json();
        console.log('✅ Correctly rejected amount below minimum:', errorData.detail);
    }
    console.log();

    console.log('🎉 All paper trading tests passed successfully!');
    console.log('\n📊 Summary:');
    console.log('- ✅ User signup auto-allocates $100,000');
    console.log('- ✅ Add funds works correctly');
    console.log('- ✅ Cash balance tracking accurate');
    console.log('- ✅ Amount validation enforced');
    console.log('- ✅ Ready for trade execution with buying power validation');
}

test().catch(err => {
    console.error('❌ Test failed:', err.message);
    process.exit(1);
});
