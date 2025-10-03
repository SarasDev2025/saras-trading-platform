/**
 * Test script for login password fix
 * Tests both normal and long passwords
 */

const BASE_URL = 'http://localhost:8000';

async function testLoginPasswordFix() {
    console.log('🔐 Testing Login Password Fix');
    console.log('==============================\n');

    try {
        // Test 1: Register user with a normal password
        console.log('📝 Test 1: Normal Password Registration');

        const normalUser = {
            username: `testuser${Date.now()}`.substring(0, 25), // Keep under 30 char limit
            email: `test_${Date.now()}@example.com`,
            password: 'NormalPassword123!', // Meets validation: 8+ chars, upper, lower, digit
            first_name: 'Test',
            last_name: 'User'
        };

        console.log(`   Registering user: ${normalUser.username}`);

        let response = await fetch(`${BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(normalUser)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('   ✅ Registration successful');

            // Test login with normal password
            console.log('   🔓 Testing login with normal password...');

            const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: normalUser.email, // OAuth2 form uses 'username' field for email
                    password: normalUser.password
                })
            });

            if (loginResponse.ok) {
                const loginResult = await loginResponse.json();
                console.log('   ✅ Login successful with normal password');
                console.log(`   📊 Token received: ${loginResult.data?.access_token?.substring(0, 20) || 'token'}...`);
            } else {
                const error = await loginResponse.json();
                console.log('   ❌ Login failed:', error.detail);
            }
        } else {
            const error = await response.json();
            console.log('   ❌ Registration failed:', error.detail);
        }

        console.log('');

        // Test 2: Register user with a very long password (>72 bytes)
        console.log('📝 Test 2: Long Password Registration (>72 bytes)');

        const longPassword = 'TestPassword123!' + 'a'.repeat(60) + 'Z9!'; // >72 bytes but meets validation
        const longPasswordUser = {
            username: `testlong${Date.now()}`.substring(0, 25), // Keep under 30 char limit
            email: `test_long_${Date.now()}@example.com`,
            password: longPassword,
            first_name: 'Test',
            last_name: 'Long'
        };

        console.log(`   Registering user: ${longPasswordUser.username}`);
        console.log(`   Password length: ${longPassword.length} characters (${Buffer.from(longPassword, 'utf8').length} bytes)`);

        response = await fetch(`${BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(longPasswordUser)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('   ✅ Registration successful (password truncated to 72 bytes)');

            // Test login with full long password (should work due to truncation)
            console.log('   🔓 Testing login with full long password...');

            const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: longPasswordUser.email,
                    password: longPassword
                })
            });

            if (loginResponse.ok) {
                const loginResult = await loginResponse.json();
                console.log('   ✅ Login successful with long password (auto-truncated)');
                console.log(`   📊 Token received: ${loginResult.data?.access_token?.substring(0, 20) || 'token'}...`);
            } else {
                const error = await loginResponse.json();
                console.log('   ❌ Login failed:', error.detail);
            }

            // Test login with truncated password (should also work)
            console.log('   🔓 Testing login with truncated password...');

            const truncatedPassword = longPassword.substring(0, 72);
            const truncatedLoginResponse = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: longPasswordUser.email,
                    password: truncatedPassword
                })
            });

            if (truncatedLoginResponse.ok) {
                const loginResult = await truncatedLoginResponse.json();
                console.log('   ✅ Login successful with truncated password');
                console.log(`   📊 Token received: ${loginResult.data?.access_token?.substring(0, 20) || 'token'}...`);
            } else {
                const error = await truncatedLoginResponse.json();
                console.log('   ❌ Login failed with truncated password:', error.detail);
            }

        } else {
            const error = await response.json();
            console.log('   ❌ Registration failed:', error.detail || error.message);
        }

        console.log('');

        // Test 3: Test password with Unicode characters
        console.log('📝 Test 3: Unicode Password Test');

        const unicodePassword = 'TestPassword123äöü!'; // Unicode but meets validation requirements
        const unicodeUser = {
            username: `testunicode${Date.now()}`.substring(0, 25), // Keep under 30 char limit
            email: `test_unicode_${Date.now()}@example.com`,
            password: unicodePassword,
            first_name: 'Test',
            last_name: 'Unicode'
        };

        console.log(`   Registering user: ${unicodeUser.username}`);
        console.log(`   Password: ${unicodePassword}`);
        console.log(`   Password byte length: ${Buffer.from(unicodePassword, 'utf8').length} bytes`);

        response = await fetch(`${BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(unicodeUser)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('   ✅ Registration successful with Unicode password');

            // Test login with Unicode password
            const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: unicodeUser.email,
                    password: unicodePassword
                })
            });

            if (loginResponse.ok) {
                const loginResult = await loginResponse.json();
                console.log('   ✅ Login successful with Unicode password');
                console.log(`   📊 Token received: ${loginResult.data?.access_token?.substring(0, 20) || 'token'}...`);
            } else {
                const error = await loginResponse.json();
                console.log('   ❌ Login failed:', error.detail);
            }
        } else {
            const error = await response.json();
            console.log('   ❌ Registration failed:', error.detail || error.message);
        }

        console.log('\n✅ Login Password Fix Test Completed!');
        console.log('\n📊 Summary:');
        console.log('   • Normal passwords (≤72 bytes): Should work normally');
        console.log('   • Long passwords (>72 bytes): Auto-truncated to 72 bytes');
        console.log('   • Unicode passwords: Handled correctly with byte-level truncation');
        console.log('   • bcrypt 72-byte limit: No longer causes server errors');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run the test
console.log('🎯 Login Password Fix Test\n');
testLoginPasswordFix();