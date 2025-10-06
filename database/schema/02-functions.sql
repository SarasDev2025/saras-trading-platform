--
-- Database Functions
--
-- This file contains all database functions used for triggers and automation
--

CREATE FUNCTION public.initialize_virtual_money() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Create virtual money config for new user
    INSERT INTO virtual_money_config (user_id, initial_allocation)
    VALUES (NEW.id, 100000.00);

    -- Create paper trading stats record
    INSERT INTO paper_trading_stats (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$;


CREATE FUNCTION public.update_last_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.last_activity = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


CREATE FUNCTION public.update_paper_trading_stats() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Update stats when a paper order is filled
    IF NEW.status = 'filled' AND OLD.status != 'filled' THEN
        INSERT INTO paper_trading_stats (user_id, total_trades)
        VALUES (NEW.user_id, 1)
        ON CONFLICT (user_id) DO UPDATE
        SET total_trades = paper_trading_stats.total_trades + 1,
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$;


CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


