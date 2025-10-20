/* Create a trigger function which automatically creates a binder in the binders table
which has slot_ids equal to the amount of slots the binder has, each of these slot id's has 
the uniqure binder_id from the collection table
 */

CREATE OR REPLACE FUNCTION binder_slots_trg_func()
RETURNS TRIGGER
LANGUAGE 'plpgsql'
AS 
$$
DECLARE
    i INTEGER; --loop counter for creating slots
BEGIN

    --loop from 1 to the number of slots specified in the new collection row
    FOR i IN 1..NEW.slots LOOP
        --insert a row into the binders table
        INSERT INTO binders (binder_id, slot_id)
        VALUES (NEW.binder_id, i);
    END LOOP;
    --return the new row(important for BEFORE triggers)
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS binder_slots_trigger on public.collection;

--attach the trigger function to the collection table
CREATE TRIGGER binder_slots_trigger
AFTER INSERT ON collection
FOR EACH ROW
EXECUTE FUNCTION binder_slots_trg_func();

/*Create a trigger function on the collection table which adds/subtracts by 1 for the count in the users table whenever a new binder is created or deleted*/
CREATE OR REPLACE FUNCTION binder_count_trg_func()
RETURNS TRIGGER
LANGUAGE 'plpgsql'
AS $$

BEGIN
    IF TG_OP = 'INSERT' THEN 
        --increment the counter for the corresponding user_id
        UPDATE users
        SET binder = COALESCE(binder, 0) + 1
        WHERE user_id = NEW.user_id;
    ELSIF TG_OP = 'DELETE' THEN
        --decrement the counter for the corresponding user_id
        UPDATE users
        SET binder = COALESCE(binder, 0) - 1
        WHERE user_id = OLD.user_id;
    END IF;
    RETURN NULL; --AFTER trigger, so return value is ignored
END;
$$;

DROP TRIGGER IF EXISTS binder_count_trg_inc on public.collection;
DROP TRIGGER IF EXISTS binder_count_trg_dec on public.collection;


CREATE TRIGGER binder_count_trg_inc
AFTER INSERT ON collection
FOR EACH ROW 
EXECUTE FUNCTION binder_count_trg_func();

CREATE TRIGGER binder_count_trg_dec
AFTER DELETE ON collection
FOR EACH ROW 
EXECUTE FUNCTION binder_count_trg_func();




/* Create a trigger function which automatically updates the cost and total_mv
when there is an update to the binder's mv and cost(linked by the binder_id)
*/

CREATE OR REPLACE FUNCTION collection_val_trg_func()
RETURNS TRIGGER
LANGUAGE 'plpgsql'
AS $$
DECLARE
    total NUMERIC;
BEGIN
    /*if there has been an update to the market value to a card, based on the binder id of that card, total all the cards market value with that binder id and set that to
    market value in the collection table with the corresponding binder_id
    
    need to also update the timestamp value when market value is updated*/
    
    --calculate the total market value for all rows with the same id as the updated row
    --only include rows where obtained = TRUE
    SELECT COALESCE(SUM(market_value), 0) INTO total
    FROM binders
    WHERE binder_id = NEW.binder_id AND obtained = TRUE;

    --update the total_mv in the collection table with the corressponding binder_id 
    UPDATE collection
    SET total_mv = total,
        mv_date = CURRENT_TIMESTAMP
    WHERE binder_id = NEW.binder_id;

    RETURN NULL; --AFTER trigger, so return value is ignored
END;
$$;

DROP TRIGGER IF EXISTS total_mv_collection_trigger on public.binders;

--create the trigger
CREATE TRIGGER total_mv_collection_trigger
AFTER UPDATE OF market_value ON binders
FOR EACH ROW
EXECUTE FUNCTION collection_val_trg_func();

/*create a trigger function on the binders table so that whenever there is an update to the cost, the total cost in the collection table is updated*/
CREATE OR REPLACE FUNCTION collection_cost_trg_function()
RETURNS TRIGGER 
LANGUAGE 'plpgsql'
AS $$
DECLARE 
    total NUMERIC;
BEGIN
    SELECT COALESCE(SUM(cost), 0) INTO total
    FROM binders
    WHERE binder_id = NEW.binder_id AND obtained = TRUE;

    UPDATE collection
    SET cost = total
    WHERE binder_id = NEW.binder_id;

    RETURN NULL; --AFTER trigger, so return value is ignored

END;
$$;

DROP TRIGGER IF EXISTS total_cost_collection_trigger on public.binders;

--create the trigger
CREATE TRIGGER total_cost_collection_trigger
AFTER UPDATE OF cost ON binders
FOR EACH ROW
EXECUTE FUNCTION collection_cost_trg_function();