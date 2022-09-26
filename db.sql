USE app_orders

show columns from polls_products

truncate table polls_clientcarts

select distinct category from polls_products

select count(*) from polls_clientcarts where client_id = 1


select
    polls_clientcarts.client_id as client,
    polls_products.product_name as name,
    polls_products.price as price,
    polls_clientcarts.product_id as product_id,
    COUNT(*) AS "count"
from polls_clientcarts
inner join polls_products

on polls_clientcarts.product_id = polls_products.id
where polls_clientcarts.client_id = 360375967
GROUP BY
    client,
    product_id,
    name,
    price
order by count;


insert into polls_cart_meta (client_id) values (12323)

describe polls_cart_meta;

alter table polls_orders alter priority set default 0;

alter table polls_orders change customer_id client_id varchar(100);

alter table polls_orders modify column client_id varchar(100) not null default '01091939';

create table polls_complete
    (client_id varchar(100) not null primary key,
     patient_name varchar(100) not null default 'Mr/Mrs',
     term date not null default '0000-00-00',
     term_time time not null default '00:00:00',
     description varchar(100) not null default 'no description',
     priority  tinyint(1) not null default 0,
     goods json not null default '{}',
     price int not null default 0
    )

update polls_complete set goods = '{"id_1": 1, "id_2": 2}' where client_id = 123131

select goods from polls_complete where client_id = 123131

update polls_complete set goods = json_set(goods, '$.id_1', 4) where client_id = 123131

select
    client_id as client,
    product_id as product_id,
    COUNT(*) AS "count"
from polls_clientcarts

where polls_clientcarts.client_id = 360375967
group by
    client,
    product_id
order by count;

alter table polls_orders add column if not exists
    (
    customer_id varchar(100) not null,
    patient_name varchar(100) not null,
    term date not null,
    term_tie time not null,
    descrition varchar(100) not null,
    priority tinyint(1) not null
    )

insert into polls_orders (client_id, patient_name, term, term_time, descrition, priority)
select client_id, patient_name, term, term_time, description, priority from polls_complete where client_id = 360375967;

select order_id from polls_orders order by order_id desc limit 1;


insert into polls_order_goods (order_id, product_id, quantity)
select
    6 as client,
    product_id as product_id,
    COUNT(*) AS "count"
from polls_clientcarts

where polls_clientcarts.client_id = 360375967
group by
    client,
    product_id
order by count;

select
    polls_order_goods.quantity as quantity,
    polls_products.product_name as name,
    polls_products.price as price
from polls_order_goods
inner join polls_products
on polls_order_goods.product_id = polls_products.id
where polls_order_goods.order_id = 6
group by
    name,
    price,
    quantity;





select
    polls_clients.client_name as name,
    polls_clients.client_address as adress

from polls_clients
inner join (select count(client_id) from polls_orders where client_id = 360375967 group by client_id) as a
group by
    name,
    adress





select patient_name, term, term_time, description from polls_complete where client_id = 123131;

select row_num, name, price, count from
(select row_number() over () as row_num, name, price, count from
(select
    polls_clientcarts.client_id as client,
    polls_products.product_name as name,
    polls_products.price as price,
    polls_clientcarts.product_id as product_id,
    COUNT(*) AS "count"
from polls_clientcarts
inner join polls_products
on polls_clientcarts.product_id = polls_products.id
where polls_clientcarts.client_id = 360375967
group by
    client,
    product_id,
    name,
    price) as a) as b where row_num = 1;

select count(*)
from
    (select distinct product_id
     from polls_clientcarts
     where client_id = ?) as b;


select row_num, name, price, count, product_id, client from
                    (select row_number() over() as row_num, name, price, count, product_id, client from
                    (select
                        polls_clientcarts.client_id as client,
                        polls_products.product_name as name,
                        polls_products.price as price,
                        polls_clientcarts.product_id as product_id,
                        COUNT(*) AS "count"
                    from polls_clientcarts
                    inner join polls_products
                    on polls_clientcarts.product_id = polls_products.id
                    where polls_clientcarts.client_id = 360375967
                    group by
                        client,
                        product_id,
                        name,
                        price) as a) as b;

select dense_rank() over (partition by client_id order by product_id) as den_ran, client_id, product_id from polls_clientcarts;


select
    polls_clients.client_name as client,
    polls_clients.client_address as adress,
    a.count as count
from polls_clients
inner join (select client_id, COUNT(*) AS "count" from polls_orders where client_id = 360375967 group by client_id) as a
on polls_clients.client_id = a.client_id
where polls_clients.client_id = 360375967
group by
    client,
    adress,
    count;

select row_number() over (order by client_name) as num, client_id from polls_clients;