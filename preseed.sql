CREATE DATABASE IF NOT EXISTS thunder;
USE thunder;
CREATE TABLE IF NOT EXISTS user
     (fname	VARCHAR(100), 
      lname	VARCHAR(100),
      role	VARCHAR(100),
      password	VARCHAR(100),
      username	VARCHAR(100),
      PRIMARY KEY (username));

CREATE TABLE IF NOT EXISTS nodes
     (name	VARCHAR(100), 
      address	VARCHAR(100),
      type	VARCHAR(100),
      PRIMARY KEY (name));

INSERT INTO user VALUES('Default', 'Admin', 'SUPERUSER', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin');
INSERT INTO nodes VALUES('NAS', '<IP>', 'STORAGE') on duplicate key update address='<IP>';
