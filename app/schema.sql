drop table if exists users;
create table users (
  id integer primary key autoincrement,
  email varchar,
  password varchar,
  role varchar,
  joined_on varchar,
  status varchar,
  confirmed_on varchar
);

drop table if exists tasks;
create table tasks (
  id integer primary key autoincrement,
  description varchar not null,
  created_on varchar not null,
  creator_id integer not null,
  foreign key (creator_id) references users(id)
);