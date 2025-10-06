--
-- Triggers and Indexes
--
-- This file contains all database triggers and indexes
-- organized by table
--

--
-- INDEXES
--

--
-- Indexes for assets
--

CREATE INDEX idx_assets_region ON public.assets USING btree (region);


--
-- Name: idx_assets_region_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_region_active ON public.assets USING btree (region, is_active);


CREATE INDEX idx_assets_symbol ON public.assets USING btree (symbol);


--
-- Name: idx_assets_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assets_type ON public.assets USING btree (asset_type);


--
-- Indexes for audit_logs
--

CREATE INDEX idx_audit_logs_client_ip ON public.audit_logs USING btree (client_ip);


--
-- Name: idx_audit_logs_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_event_type ON public.audit_logs USING btree (event_type);


CREATE INDEX idx_audit_logs_path ON public.audit_logs USING btree (path);


--
-- Name: idx_audit_logs_request_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_request_id ON public.audit_logs USING btree (request_id);


CREATE INDEX idx_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: idx_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Indexes for basket_orders
--

CREATE INDEX idx_basket_orders_basket_id ON public.basket_orders USING btree (basket_id);


--
-- Name: idx_basket_orders_broker_connection; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_basket_orders_broker_connection ON public.basket_orders USING btree (broker_connection_id);


CREATE INDEX idx_basket_orders_created_at ON public.basket_orders USING btree (created_at);


--
-- Name: idx_basket_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_basket_orders_status ON public.basket_orders USING btree (status, is_active);


--
-- Indexes for dividend_bulk_orders
--

CREATE INDEX idx_dividend_bulk_orders_date ON public.dividend_bulk_orders USING btree (execution_date);


--
-- Name: idx_dividend_bulk_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dividend_bulk_orders_status ON public.dividend_bulk_orders USING btree (status);


--
-- Indexes for dividend_declarations
--

CREATE INDEX idx_dividend_declarations_asset_ex_date ON public.dividend_declarations USING btree (asset_id, ex_dividend_date);


--
-- Name: idx_dividend_declarations_payment_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dividend_declarations_payment_date ON public.dividend_declarations USING btree (payment_date);


--
-- Indexes for drip_bulk_order_allocations
--

CREATE INDEX idx_drip_bulk_allocations_bulk ON public.drip_bulk_order_allocations USING btree (dividend_bulk_order_id);


--
-- Name: idx_drip_bulk_allocations_drip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drip_bulk_allocations_drip ON public.drip_bulk_order_allocations USING btree (drip_transaction_id);


--
-- Indexes for drip_transactions
--

CREATE INDEX idx_drip_transactions_asset ON public.drip_transactions USING btree (asset_id);


--
-- Name: idx_drip_transactions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drip_transactions_date ON public.drip_transactions USING btree (transaction_date);


CREATE INDEX idx_drip_transactions_user ON public.drip_transactions USING btree (user_id);


--
-- Name: idx_gtt_orders_broker_connection; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gtt_orders_broker_connection ON public.gtt_orders USING btree (broker_connection_id);


--
-- Indexes for gtt_orders
--

CREATE INDEX idx_gtt_orders_created_at ON public.gtt_orders USING btree (created_at);


--
-- Name: idx_gtt_orders_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gtt_orders_expires_at ON public.gtt_orders USING btree (expires_at);


CREATE INDEX idx_gtt_orders_status ON public.gtt_orders USING btree (status, is_active);


--
-- Name: idx_gtt_orders_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gtt_orders_symbol ON public.gtt_orders USING btree (symbol);


CREATE INDEX idx_gtt_orders_trigger_id ON public.gtt_orders USING btree (trigger_id);


--
-- Name: idx_login_attempts_attempted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_attempts_attempted_at ON public.login_attempts USING btree (attempted_at);


--
-- Indexes for login_attempts
--

CREATE INDEX idx_login_attempts_client_ip ON public.login_attempts USING btree (client_ip);


--
-- Name: idx_login_attempts_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_attempts_email ON public.login_attempts USING btree (email);


CREATE INDEX idx_login_attempts_success ON public.login_attempts USING btree (success);


--
-- Name: idx_login_attempts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_attempts_user_id ON public.login_attempts USING btree (user_id);


--
-- Indexes for oco_orders
--

CREATE INDEX idx_oco_orders_broker_connection ON public.oco_orders USING btree (broker_connection_id);


--
-- Name: idx_oco_orders_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oco_orders_created_at ON public.oco_orders USING btree (created_at);


CREATE INDEX idx_oco_orders_status ON public.oco_orders USING btree (status, is_active);


--
-- Name: idx_oco_orders_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oco_orders_symbol ON public.oco_orders USING btree (symbol);


CREATE INDEX idx_oco_orders_trigger_id ON public.oco_orders USING btree (trigger_id);


--
-- Name: idx_paper_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_paper_orders_status ON public.paper_orders USING btree (status, broker_type);


--
-- Indexes for paper_orders
--

CREATE INDEX idx_paper_orders_symbol ON public.paper_orders USING btree (symbol, created_at DESC);


--
-- Name: idx_paper_orders_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_paper_orders_user ON public.paper_orders USING btree (user_id, created_at DESC);


--
-- Indexes for paper_trading_stats
--

CREATE UNIQUE INDEX idx_paper_stats_user ON public.paper_trading_stats USING btree (user_id);


--
-- Name: idx_performance_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_performance_date ON public.smallcase_performance USING btree (date);


--
-- Indexes for portfolio_holdings
--

CREATE INDEX idx_portfolio_holdings_asset_id ON public.portfolio_holdings USING btree (asset_id);


--
-- Name: idx_portfolio_holdings_portfolio_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_portfolio_holdings_portfolio_id ON public.portfolio_holdings USING btree (portfolio_id);


--
-- Indexes for portfolios
--

CREATE INDEX idx_portfolios_cash_balance ON public.portfolios USING btree (cash_balance);


--
-- Name: idx_portfolios_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_portfolios_user_id ON public.portfolios USING btree (user_id);


--
-- Indexes for price_history
--

CREATE INDEX idx_price_history_asset_id ON public.price_history USING btree (asset_id);


--
-- Name: idx_price_history_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_price_history_timestamp ON public.price_history USING btree ("timestamp");


--
-- Indexes for rate_limit_violations
--

CREATE INDEX idx_rate_limit_violations_blocked_until ON public.rate_limit_violations USING btree (blocked_until);


--
-- Name: idx_rate_limit_violations_client_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rate_limit_violations_client_ip ON public.rate_limit_violations USING btree (client_ip);


CREATE INDEX idx_rate_limit_violations_created_at ON public.rate_limit_violations USING btree (created_at);


--
-- Name: idx_rate_limit_violations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rate_limit_violations_user_id ON public.rate_limit_violations USING btree (user_id);


--
-- Indexes for refresh_tokens
--

CREATE INDEX idx_refresh_tokens_expires_at ON public.refresh_tokens USING btree (expires_at);


--
-- Name: idx_refresh_tokens_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refresh_tokens_token_hash ON public.refresh_tokens USING btree (token_hash);


CREATE INDEX idx_refresh_tokens_user_id ON public.refresh_tokens USING btree (user_id);


--
-- Name: idx_security_logs_client_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_security_logs_client_ip ON public.security_logs USING btree (client_ip);


--
-- Indexes for security_logs
--

CREATE INDEX idx_security_logs_event_type ON public.security_logs USING btree (event_type);


--
-- Name: idx_security_logs_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_security_logs_severity ON public.security_logs USING btree (severity);


CREATE INDEX idx_security_logs_timestamp ON public.security_logs USING btree ("timestamp");


--
-- Name: idx_security_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_security_logs_user_id ON public.security_logs USING btree (user_id);


--
-- Indexes for smallcase_constituents
--

CREATE INDEX idx_constituents_weight ON public.smallcase_constituents USING btree (weight_percentage);


--
-- Name: idx_dividend_bulk_orders_asset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dividend_bulk_orders_asset ON public.dividend_bulk_orders USING btree (asset_id);


CREATE INDEX idx_smallcase_constituents_smallcase_id ON public.smallcase_constituents USING btree (smallcase_id);


--
-- Name: idx_smallcase_execution_orders_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smallcase_execution_orders_run_id ON public.smallcase_execution_orders USING btree (execution_run_id);


--
-- Indexes for smallcase_execution_runs
--

CREATE INDEX idx_smallcase_execution_runs_investment_id ON public.smallcase_execution_runs USING btree (investment_id);


--
-- Name: idx_smallcases_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smallcases_region ON public.smallcases USING btree (region);


--
-- Indexes for smallcases
--

CREATE INDEX idx_smallcases_region_active ON public.smallcases USING btree (region, is_active);


--
-- Name: idx_smallcases_risk_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smallcases_risk_level ON public.smallcases USING btree (risk_level);


--
-- Indexes for suspicious_activities
--

CREATE INDEX idx_suspicious_activities_activity_type ON public.suspicious_activities USING btree (activity_type);


--
-- Name: idx_suspicious_activities_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_suspicious_activities_created_at ON public.suspicious_activities USING btree (created_at);


CREATE INDEX idx_suspicious_activities_investigated ON public.suspicious_activities USING btree (investigated);


--
-- Name: idx_suspicious_activities_risk_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_suspicious_activities_risk_score ON public.suspicious_activities USING btree (risk_score);


CREATE INDEX idx_suspicious_activities_user_id ON public.suspicious_activities USING btree (user_id);


--
-- Name: idx_token_blacklist_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_blacklist_expires_at ON public.token_blacklist USING btree (expires_at);


--
-- Indexes for token_blacklist
--

CREATE INDEX idx_token_blacklist_token_hash ON public.token_blacklist USING btree (token_hash);


--
-- Name: idx_token_blacklist_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_blacklist_user_id ON public.token_blacklist USING btree (user_id);


--
-- Indexes for token_validations
--

CREATE INDEX idx_token_validations_client_ip ON public.token_validations USING btree (client_ip);


--
-- Name: idx_token_validations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_validations_created_at ON public.token_validations USING btree (created_at);


CREATE INDEX idx_token_validations_result ON public.token_validations USING btree (result);


--
-- Name: idx_token_validations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_token_validations_user_id ON public.token_validations USING btree (user_id);


--
-- Indexes for trading_transactions
--

CREATE INDEX idx_trading_transactions_asset_id ON public.trading_transactions USING btree (asset_id);


--
-- Name: idx_trading_transactions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trading_transactions_date ON public.trading_transactions USING btree (transaction_date);


CREATE INDEX idx_trading_transactions_external_id ON public.trading_transactions USING btree (external_transaction_id);


--
-- Name: idx_trading_transactions_portfolio_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trading_transactions_portfolio_id ON public.trading_transactions USING btree (portfolio_id);


CREATE INDEX idx_trading_transactions_status ON public.trading_transactions USING btree (status);


--
-- Name: idx_trading_transactions_transaction_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trading_transactions_transaction_type ON public.trading_transactions USING btree (transaction_type);


CREATE INDEX idx_trading_transactions_user_created ON public.trading_transactions USING btree (user_id, created_at DESC);


--
-- Name: idx_trading_transactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trading_transactions_user_id ON public.trading_transactions USING btree (user_id);


--
-- Indexes for user_broker_connections
--

CREATE INDEX idx_user_broker_connections_broker_type ON public.user_broker_connections USING btree (broker_type);


--
-- Name: idx_user_broker_connections_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_broker_connections_user_id ON public.user_broker_connections USING btree (user_id);


--
-- Indexes for user_dividend_payments
--

CREATE INDEX idx_dividend_payments_asset ON public.user_dividend_payments USING btree (asset_id);


--
-- Name: idx_dividend_payments_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dividend_payments_date ON public.user_dividend_payments USING btree (payment_date);


CREATE INDEX idx_dividend_payments_status ON public.user_dividend_payments USING btree (status);


--
-- Name: idx_dividend_payments_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dividend_payments_user ON public.user_dividend_payments USING btree (user_id);


--
-- Indexes for user_drip_preferences
--

CREATE INDEX idx_drip_preferences_asset ON public.user_drip_preferences USING btree (asset_id);


--
-- Name: idx_drip_preferences_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drip_preferences_user ON public.user_drip_preferences USING btree (user_id);


--
-- Indexes for user_position_snapshots
--

CREATE INDEX idx_position_snapshots_dividend ON public.user_position_snapshots USING btree (dividend_declaration_id);


--
-- Name: idx_position_snapshots_user_asset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_position_snapshots_user_asset ON public.user_position_snapshots USING btree (user_id, asset_id);


--
-- Indexes for user_sessions
--

CREATE INDEX idx_user_sessions_expires_at ON public.user_sessions USING btree (expires_at);


--
-- Name: idx_user_sessions_session_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_sessions_session_token ON public.user_sessions USING btree (session_token);


CREATE INDEX idx_user_sessions_token ON public.user_sessions USING btree (session_token);


--
-- Name: idx_user_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_sessions_user_id ON public.user_sessions USING btree (user_id);


--
-- Indexes for user_smallcase_investments
--

CREATE INDEX idx_user_smallcase_investments_broker_connection_id ON public.user_smallcase_investments USING btree (broker_connection_id);


--
-- Name: idx_user_smallcase_investments_closed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_smallcase_investments_closed_at ON public.user_smallcase_investments USING btree (closed_at) WHERE (closed_at IS NOT NULL);


CREATE INDEX idx_user_smallcase_investments_status_closed ON public.user_smallcase_investments USING btree (user_id, status) WHERE ((status)::text = ANY ((ARRAY['sold'::character varying, 'partial'::character varying])::text[]));


--
-- Name: idx_user_smallcase_investments_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_smallcase_investments_user_id ON public.user_smallcase_investments USING btree (user_id);


--
-- Indexes for user_smallcase_position_history
--

CREATE INDEX idx_position_history_closed_at ON public.user_smallcase_position_history USING btree (closed_at);


--
-- Name: idx_position_history_smallcase_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_position_history_smallcase_id ON public.user_smallcase_position_history USING btree (smallcase_id);


CREATE INDEX idx_position_history_user_id ON public.user_smallcase_position_history USING btree (user_id);


--
-- Name: idx_position_snapshots_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_position_snapshots_date ON public.user_position_snapshots USING btree (snapshot_date);


--
-- Indexes for users
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_email_verification_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email_verification_token ON public.users USING btree (email_verification_token);


CREATE INDEX idx_users_password_reset_token ON public.users USING btree (password_reset_token);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Indexes for virtual_money_config
--

CREATE INDEX idx_virtual_money_user ON public.virtual_money_config USING btree (user_id);


--
-- Name: users trigger_init_virtual_money; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_init_virtual_money AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.initialize_virtual_money();




--
-- TRIGGERS
--

--
-- Triggers for basket_orders
--

CREATE TRIGGER update_basket_orders_updated_at BEFORE UPDATE ON public.basket_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: gtt_orders update_gtt_orders_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_gtt_orders_updated_at BEFORE UPDATE ON public.gtt_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for oco_orders
--

CREATE TRIGGER update_oco_orders_updated_at BEFORE UPDATE ON public.oco_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: portfolio_holdings update_portfolio_holdings_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_portfolio_holdings_updated_at BEFORE UPDATE ON public.portfolio_holdings FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for paper_orders
--

CREATE TRIGGER trigger_update_paper_stats AFTER UPDATE ON public.paper_orders FOR EACH ROW EXECUTE FUNCTION public.update_paper_trading_stats();


--
-- Name: assets update_assets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON public.assets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for portfolios
--

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON public.portfolios FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: smallcase_constituents update_smallcase_constituents_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_smallcase_constituents_updated_at BEFORE UPDATE ON public.smallcase_constituents FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for smallcase_execution_orders
--

CREATE TRIGGER update_smallcase_execution_orders_updated_at BEFORE UPDATE ON public.smallcase_execution_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: smallcase_execution_runs update_smallcase_execution_runs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_smallcase_execution_runs_updated_at BEFORE UPDATE ON public.smallcase_execution_runs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for smallcases
--

CREATE TRIGGER update_smallcases_updated_at BEFORE UPDATE ON public.smallcases FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: trading_transactions update_trading_transactions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_trading_transactions_updated_at BEFORE UPDATE ON public.trading_transactions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for user_broker_connections
--

CREATE TRIGGER update_user_broker_connections_updated_at BEFORE UPDATE ON public.user_broker_connections FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_sessions update_user_sessions_last_activity; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_sessions_last_activity BEFORE UPDATE ON public.user_sessions FOR EACH ROW EXECUTE FUNCTION public.update_last_activity();


--
-- Triggers for user_smallcase_investments
--

CREATE TRIGGER update_user_smallcase_investments_updated_at BEFORE UPDATE ON public.user_smallcase_investments FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_smallcase_position_history update_user_smallcase_position_history_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_smallcase_position_history_updated_at BEFORE UPDATE ON public.user_smallcase_position_history FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Triggers for users
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


