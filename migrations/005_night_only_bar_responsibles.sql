ALTER TABLE bars MODIFY responsible_user_id INT NULL;
UPDATE bars SET responsible_user_id = NULL;
