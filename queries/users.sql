CREATE TABLE users (
    user_id SERIAL PRIMARY KEY, 
    username VARCHAR (255) NOT NULL UNIQUE,
    passphrase VARCHAR (255) NOT NULL,
    binder INTEGER NULL CHECK (binder <= 9)
);