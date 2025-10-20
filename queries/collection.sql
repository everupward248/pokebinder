CREATE TABLE collection (
    user_id INT, 
    binder_id SERIAL PRIMARY KEY,
    sheets INT NOT NULL CHECK (sheets  BETWEEN 1 AND 30), 
    pages INT NOT NULL CHECK (pages BETWEEN 1 AND 60), 
    binder_rows INT NOT NULL CHECK (binder_rows BETWEEN 1 AND 5), 
    binder_columns INT NOT NULL CHECK (binder_columns BETWEEN 1 AND 7), 
    slots INT NULL CHECK (slots > 0),
    total_mv NUMERIC DEFAULT 0 CHECK (total_mv >= 0),
    cost NUMERIC DEFAULT 0 CHECK (cost >= 0),
    mv_date TIMESTAMP NULL,
    img_url TEXT DEFAULT 'static/binder.jpg',
    name VARCHAR(30) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE
);