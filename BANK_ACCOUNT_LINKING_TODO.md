# Bank Account Linking & Real Cash Investment - TODO Plan

## Overview
Implementation roadmap for adding bank account linking and real cash investment capabilities to support both US and India markets, building on existing broker selection infrastructure.

## Current Status
- ✅ **Broker Selection**: US (Alpaca) and India (Zerodha) broker integration working
- ✅ **Paper Trading**: Investment creation and portfolio management functional
- ❌ **Real Money**: Bank account linking and cash management not implemented

---

## TODO List - Bank Account Linking Implementation

### 🏗️ **Infrastructure & Architecture**

- [ ] **Research and design multi-regional bank account linking architecture**
  - Study Plaid Link (US) vs Account Aggregator (India) approaches
  - Design unified API interface for regional payment providers
  - Plan data flow: Bank → Platform → Broker integration

- [ ] **Design database schema for regional payment systems (US ACH, India UPI/NEFT)**
  - Create `user_bank_accounts` table with regional fields
  - Add `cash_transactions` table supporting multiple payment methods
  - Extend `portfolios` table with currency and region tracking
  - Add compliance and audit tables for regulatory requirements

### 🇺🇸 **US Market Integration**

- [ ] **Integrate US payment stack - Plaid Link for bank verification**
  - Set up Plaid developer account and API keys
  - Implement Plaid Link frontend integration
  - Handle bank account verification and micro-deposits
  - Store encrypted bank account information

- [ ] **Integrate US ACH processing via Dwolla API**
  - Set up Dwolla sandbox and production environments
  - Implement ACH deposit workflow (3-5 day settlement)
  - Build ACH withdrawal system with compliance checks
  - Handle failed transactions and retry logic

- [ ] **Connect real money flow to existing Alpaca broker integration (US)**
  - Upgrade from paper trading to live Alpaca accounts
  - Implement cash transfer from portfolio to Alpaca
  - Sync portfolio cash balance with broker account
  - Handle trade settlements and cash management

### 🇮🇳 **India Market Integration**

- [ ] **Integrate India payment stack - Razorpay for UPI/NEFT/cards**
  - Set up Razorpay merchant account and API integration
  - Implement UPI payment flow (instant settlements)
  - Add NEFT/RTGS bank transfer options (2-4 hour settlement)
  - Support major Indian banks and payment methods

- [ ] **Implement Account Aggregator framework for India bank linking**
  - Research RBI's Account Aggregator ecosystem
  - Integrate with AA providers (YODLEE India, FinBox)
  - Implement consent-based bank account linking
  - Handle AA data formatting and verification

- [ ] **Connect real money flow to existing Zerodha broker integration (India)**
  - Upgrade from paper trading to live Zerodha accounts
  - Implement cash transfer from portfolio to Zerodha
  - Handle INR currency and Indian market hours
  - Sync with Zerodha's fund management APIs

### 💰 **Core Financial Features**

- [ ] **Implement multi-currency portfolio management (USD/INR)**
  - Add currency field to portfolio table and models
  - Implement currency-specific investment minimums
  - Build currency conversion capabilities for display
  - Handle regional asset restrictions (US stocks vs Indian stocks)

- [ ] **Build deposit workflow - bank link to portfolio funding**
  - Create unified deposit API for both regions
  - Implement deposit amount validation and limits
  - Build real-time balance updates and notifications
  - Add deposit history and transaction tracking

- [ ] **Build withdrawal workflow - portfolio to bank transfer**
  - Implement withdrawal request system with approvals
  - Add security checks and daily/monthly limits
  - Build withdrawal scheduling and processing queue
  - Create withdrawal confirmation and status tracking

- [ ] **Add instant funding capabilities (credit line while ACH/transfers settle)**
  - Research instant funding providers (US: Dwolla, India: PayU)
  - Implement credit line assessment and approval
  - Build instant funding UI with clear terms disclosure
  - Handle credit line repayment when deposits settle

- [ ] **Implement cash sweep to high-yield accounts for uninvested funds**
  - Research high-yield partners (US: Goldman Sachs, India: HDFC/ICICI)
  - Build automatic cash sweep based on idle time
  - Implement instant withdrawal from sweep accounts
  - Add yield tracking and interest payments

### 📋 **Regulatory Compliance**

- [ ] **Implement US regulatory compliance (Money Transmitter License, BSA/AML)**
  - Research state-by-state MTL requirements (50+ licenses needed)
  - Implement BSA reporting and suspicious activity monitoring
  - Add OFAC sanctions screening for all transactions
  - Build audit trails for regulatory examinations

- [ ] **Implement India regulatory compliance (RBI guidelines, PMLA)**
  - Research RBI Payment Aggregator licensing requirements
  - Implement PMLA compliance and transaction monitoring
  - Add Aadhaar-based KYC verification enhancements
  - Build GST reporting for financial services

- [ ] **Setup fraud detection and transaction monitoring systems**
  - Implement velocity checks and unusual pattern detection
  - Add device fingerprinting and location verification
  - Build manual review queue for suspicious transactions
  - Create automated risk scoring for all cash movements

### 🎨 **User Experience & Frontend**

- [ ] **Build regional payment UI/UX (Plaid Link for US, UPI for India)**
  - Create region-specific bank linking flows
  - Design mobile-optimized UPI QR code interface
  - Build bank account management dashboard
  - Add payment method selection and preferences

- [ ] **Test end-to-end real money investment flow for both regions**
  - Create comprehensive test cases for both markets
  - Test deposit → invest → trade → withdraw full cycle
  - Validate currency handling and broker integration
  - Test error scenarios and edge cases

---

## Implementation Phases

### **Phase 1: Foundation (Weeks 1-4)**
- Database schema design and migration
- Regional architecture planning
- US Plaid Link integration
- India Razorpay basic integration

### **Phase 2: Core Features (Weeks 5-8)**
- Deposit/withdrawal workflows
- Multi-currency portfolio support
- Broker real-money integration
- Basic compliance framework

### **Phase 3: Advanced Features (Weeks 9-12)**
- Instant funding capabilities
- Cash sweep functionality
- Enhanced fraud detection
- Comprehensive testing

### **Phase 4: Regulatory & Launch (Weeks 13-16)**
- Full compliance implementation
- Regulatory approval processes
- Production deployment
- User onboarding and support

---

## Key Dependencies

### **External Services**
- **US**: Plaid (bank linking), Dwolla (ACH), Alpaca (trading)
- **India**: Razorpay (payments), Account Aggregator, Zerodha (trading)

### **Regulatory Approvals**
- **US**: Money Transmitter Licenses (12-18 months)
- **India**: RBI Payment Aggregator License (6-12 months)

### **Technical Infrastructure**
- Enhanced database security and encryption
- PCI DSS compliance for payment data
- Regional data residency requirements
- 24/7 monitoring and support systems

---

## Success Metrics

### **User Experience**
- Bank account linking success rate >85%
- Average deposit time <24 hours (US), <2 hours (India)
- Customer support response time <2 hours

### **Regulatory Compliance**
- Zero compliance violations in first 12 months
- 100% transaction monitoring coverage
- Successful regulatory audits and examinations

### **Business Metrics**
- Real money adoption rate >60% of paper trading users
- Average deposit amount >$10,000 (US), >₹5,00,000 (India)
- Customer acquisition cost recovery within 6 months

---

## Notes

This implementation builds on the existing broker selection infrastructure that correctly routes:
- US users (.com emails) → Alpaca broker
- India users (.in emails, gmail.com) → Zerodha broker

The todo list is prioritized to maintain this regional architecture while adding real money capabilities.