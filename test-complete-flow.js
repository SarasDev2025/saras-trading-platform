async function testCompleteFlow() {
  console.log("🧪 Testing Complete Investment → Holdings → Closure Flow");
  
  const loginResponse = await fetch("http://localhost:8000/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "username=john.doe@example.com&password=password123"
  });
  const loginData = await loginResponse.json();
  const token = loginData.access_token || loginData.data?.access_token;
  console.log("✅ Authentication successful");
  
  // Get available smallcases
  const smallcasesResponse = await fetch("http://localhost:8000/smallcases/", {
    headers: { "Authorization": `Bearer ${token}` }
  });
  const smallcasesData = await smallcasesResponse.json();
  const availableSmallcases = smallcasesData.data.filter(sc => !sc.isInvested);
  const testSmallcase = availableSmallcases[0];
  console.log(`📊 Selected smallcase: ${testSmallcase.name}`);
  
  // Create investment
  const investmentAmount = Math.max(testSmallcase.minimumInvestment, 5000);
  const investResponse = await fetch(`http://localhost:8000/smallcases/${testSmallcase.id}/invest`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      amount: investmentAmount,
      execution_mode: "paper"
    })
  });
  
  if (!investResponse.ok) {
    const errorData = await investResponse.json();
    console.error("❌ Investment failed:", errorData);
    return;
  }
  
  const investData = await investResponse.json();
  console.log("✅ Investment created successfully");
  console.log(`💵 Investment amount: $${investmentAmount}`);
  console.log(`📊 Holdings created: ${investData.data.holdingsCreated}`);
  
  // Test closure preview directly with investment ID
  const investmentId = investData.data.investmentId;
  console.log(`🔍 Testing closure preview for investment: ${investmentId}`);
  
  const closureResponse = await fetch(`http://localhost:8000/smallcases/investments/${investmentId}/closure-preview`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  
  if (closureResponse.ok) {
    const closureData = await closureResponse.json();
    console.log("✅ Closure preview successful - holdings found!");
    console.log(`💰 Current value: $${closureData.data.current_value}`);
    console.log(`📊 Holdings to close: ${closureData.data.holdings_to_close?.length || 0}`);
    return { success: true, investment: investData.data, closure: closureData.data };
  } else {
    const errorData = await closureResponse.json();
    console.log("❌ Closure preview failed:", errorData);
    return { error: errorData, investment: investData.data };
  }
}

testCompleteFlow().then(result => {
  console.log("\n" + "=".repeat(50));
  if (result?.success) {
    console.log("🎉 SUCCESS: Complete investment and closure flow working!");
  } else if (result?.error) {
    console.log("❌ CLOSURE FAILED: Holdings may not be properly created");
  }
}).catch(console.error);
