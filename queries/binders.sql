CREATE TABLE binders (
    binder_id INT,
    slot_id INT,
    set_name VARCHAR(255) NULL,
    set_id VARCHAR(255) NULL,
    card_name VARCHAR(255) NULL, 
    card_number VARCHAR(255) NULL,
    card_id VARCHAR(255) NULL,
    market_value NUMERIC DEFAULT 0 CHECK (market_value >= 0),
    cost NUMERIC DEFAULT 0 CHECK (cost >= 0),
    image_url TEXT DEFAULT 'static/card_back.jpg',
    obtained BOOLEAN DEFAULT FALSE, 
    obtained_at TIMESTAMP NULL, 
    timestamp_mv TIMESTAMP NULL,
    FOREIGN KEY (binder_id) REFERENCES collection(binder_id)
    ON DELETE CASCADE
);

/* ON DELETE CASCADE so that when a binder_id is deleted from the collection table, all items with that binder_id are deleted from the binder table
 once a binder is created, its dimensions and id are stored in the collection table
 for the binder, slot_ids are created for the amount of slots in the binder, for each of these rows they are linked to the binder_id(fk)
 default values for the image and obtained
*/

/*this is a child table in a one-to-many and has no primary key