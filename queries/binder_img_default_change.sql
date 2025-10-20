/* Alter the default value for the image_url in the binders table*/

ALTER TABLE binders ALTER COLUMN image_url SET DEFAULT 'static/cardBack.jpg';
