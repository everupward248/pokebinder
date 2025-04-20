--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

-- Started on 2025-04-19 21:10:46

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 222 (class 1255 OID 16519)
-- Name: binder_count_trg_func(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.binder_count_trg_func() RETURNS trigger
    LANGUAGE plpgsql
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


ALTER FUNCTION public.binder_count_trg_func() OWNER TO postgres;

--
-- TOC entry 224 (class 1255 OID 16516)
-- Name: binder_slots_trg_func(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.binder_slots_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


ALTER FUNCTION public.binder_slots_trg_func() OWNER TO postgres;

--
-- TOC entry 223 (class 1255 OID 16526)
-- Name: collection_cost_trg_function(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.collection_cost_trg_function() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE 
    total NUMERIC;
BEGIN
    SELECT COALESCE(SUM(cost, 0)) INTO total
    FROM binders
    WHERE binder_id = NEW.binder_id AND obtained = TRUE;

    UPDATE collection
    SET cost = total
    WHERE binder_id = NEW.binder_id;

    RETURN NULL; --AFTER trigger, so return value is ignored

END;
$$;


ALTER FUNCTION public.collection_cost_trg_function() OWNER TO postgres;

--
-- TOC entry 236 (class 1255 OID 16522)
-- Name: collection_val_trg_func(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.collection_val_trg_func() RETURNS trigger
    LANGUAGE plpgsql
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


ALTER FUNCTION public.collection_val_trg_func() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 16498)
-- Name: binders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.binders (
    binder_id integer,
    slot_id integer,
    set_name character varying(255),
    set_id character varying(255),
    card_name character varying(255),
    card_number character varying(255),
    card_id character varying(255),
    market_value numeric DEFAULT 0,
    cost numeric DEFAULT 0,
    image_url text DEFAULT 'static/cardBack.jpg'::text,
    obtained boolean DEFAULT false,
    obtained_at timestamp without time zone,
    timestamp_mv timestamp without time zone,
    CONSTRAINT binders_cost_check CHECK ((cost >= (0)::numeric)),
    CONSTRAINT binders_market_value_check CHECK ((market_value >= (0)::numeric))
);


ALTER TABLE public.binders OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16452)
-- Name: collection; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collection (
    user_id integer,
    binder_id integer NOT NULL,
    sheets integer NOT NULL,
    pages integer NOT NULL,
    binder_rows integer NOT NULL,
    binder_columns integer NOT NULL,
    slots integer,
    total_mv numeric DEFAULT 0,
    cost numeric DEFAULT 0,
    mv_date timestamp without time zone,
    img_url text DEFAULT 'static/binder.jpg'::text,
    name character varying(30) NOT NULL,
    CONSTRAINT collection_binder_columns_check CHECK (((binder_columns >= 1) AND (binder_columns <= 7))),
    CONSTRAINT collection_binder_rows_check CHECK (((binder_rows >= 1) AND (binder_rows <= 5))),
    CONSTRAINT collection_cost_check CHECK ((cost >= (0)::numeric)),
    CONSTRAINT collection_pages_check CHECK (((pages >= 1) AND (pages <= 60))),
    CONSTRAINT collection_sheets_check CHECK (((sheets >= 1) AND (sheets <= 30))),
    CONSTRAINT collection_slots_check CHECK ((slots > 0)),
    CONSTRAINT collection_total_mv_check CHECK ((total_mv >= (0)::numeric))
);


ALTER TABLE public.collection OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16451)
-- Name: collection_binder_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collection_binder_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collection_binder_id_seq OWNER TO postgres;

--
-- TOC entry 4895 (class 0 OID 0)
-- Dependencies: 219
-- Name: collection_binder_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collection_binder_id_seq OWNED BY public.collection.binder_id;


--
-- TOC entry 218 (class 1259 OID 16401)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(255) NOT NULL,
    passphrase character varying(255) NOT NULL,
    binder integer,
    CONSTRAINT users_binder_check CHECK ((binder <= 9))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16400)
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- TOC entry 4896 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- TOC entry 4709 (class 2604 OID 16455)
-- Name: collection binder_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collection ALTER COLUMN binder_id SET DEFAULT nextval('public.collection_binder_id_seq'::regclass);


--
-- TOC entry 4708 (class 2604 OID 16404)
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- TOC entry 4889 (class 0 OID 16498)
-- Dependencies: 221
-- Data for Name: binders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.binders (binder_id, slot_id, set_name, set_id, card_name, card_number, card_id, market_value, cost, image_url, obtained, obtained_at, timestamp_mv) FROM stdin;
\.


--
-- TOC entry 4888 (class 0 OID 16452)
-- Dependencies: 220
-- Data for Name: collection; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collection (user_id, binder_id, sheets, pages, binder_rows, binder_columns, slots, total_mv, cost, mv_date, img_url, name) FROM stdin;
\.


--
-- TOC entry 4886 (class 0 OID 16401)
-- Dependencies: 218
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, passphrase, binder) FROM stdin;
\.


--
-- TOC entry 4897 (class 0 OID 0)
-- Dependencies: 219
-- Name: collection_binder_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collection_binder_id_seq', 1, false);


--
-- TOC entry 4898 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1, false);


--
-- TOC entry 4732 (class 2606 OID 16469)
-- Name: collection collection_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collection
    ADD CONSTRAINT collection_pkey PRIMARY KEY (binder_id);


--
-- TOC entry 4728 (class 2606 OID 16409)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4730 (class 2606 OID 16411)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 4735 (class 2620 OID 16521)
-- Name: collection binder_count_trg_dec; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER binder_count_trg_dec AFTER DELETE ON public.collection FOR EACH ROW EXECUTE FUNCTION public.binder_count_trg_func();


--
-- TOC entry 4736 (class 2620 OID 16520)
-- Name: collection binder_count_trg_inc; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER binder_count_trg_inc AFTER INSERT ON public.collection FOR EACH ROW EXECUTE FUNCTION public.binder_count_trg_func();


--
-- TOC entry 4737 (class 2620 OID 16540)
-- Name: collection binder_slots_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER binder_slots_trigger AFTER INSERT ON public.collection FOR EACH ROW EXECUTE FUNCTION public.binder_slots_trg_func();


--
-- TOC entry 4738 (class 2620 OID 16527)
-- Name: binders total_cost_collection_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER total_cost_collection_trigger AFTER UPDATE OF cost ON public.binders FOR EACH ROW EXECUTE FUNCTION public.collection_cost_trg_function();


--
-- TOC entry 4739 (class 2620 OID 16724)
-- Name: binders total_mv_collection_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER total_mv_collection_trigger AFTER UPDATE OF market_value ON public.binders FOR EACH ROW EXECUTE FUNCTION public.collection_val_trg_func();


--
-- TOC entry 4734 (class 2606 OID 16509)
-- Name: binders binders_binder_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.binders
    ADD CONSTRAINT binders_binder_id_fkey FOREIGN KEY (binder_id) REFERENCES public.collection(binder_id) ON DELETE CASCADE;


--
-- TOC entry 4733 (class 2606 OID 16470)
-- Name: collection collection_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collection
    ADD CONSTRAINT collection_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


-- Completed on 2025-04-19 21:10:46

--
-- PostgreSQL database dump complete
--

