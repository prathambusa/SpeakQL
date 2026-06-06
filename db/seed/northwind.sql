-- Northwind sample dataset for SpeakQL
-- Compatible with PostgreSQL 14+

-- ── Schema ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(30)  NOT NULL,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   SERIAL PRIMARY KEY,
    company_name  VARCHAR(80)  NOT NULL,
    contact_name  VARCHAR(60),
    contact_title VARCHAR(60),
    city          VARCHAR(30),
    country       VARCHAR(30),
    phone         VARCHAR(24),
    email         VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS products (
    product_id        SERIAL PRIMARY KEY,
    product_name      VARCHAR(80)    NOT NULL,
    supplier_id       INTEGER        REFERENCES suppliers(supplier_id),
    category_id       INTEGER        REFERENCES categories(category_id),
    unit_price        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    units_in_stock    INTEGER        NOT NULL DEFAULT 0,
    units_on_order    INTEGER        NOT NULL DEFAULT 0,
    reorder_level     INTEGER        NOT NULL DEFAULT 0,
    discontinued      BOOLEAN        NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   CHAR(5)      PRIMARY KEY,
    company_name  VARCHAR(80)  NOT NULL,
    contact_name  VARCHAR(60),
    contact_title VARCHAR(60),
    city          VARCHAR(30),
    country       VARCHAR(30),
    phone         VARCHAR(24),
    email         VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id   SERIAL PRIMARY KEY,
    last_name     VARCHAR(40) NOT NULL,
    first_name    VARCHAR(20) NOT NULL,
    title         VARCHAR(60),
    hire_date     DATE,
    city          VARCHAR(30),
    country       VARCHAR(30),
    reports_to    INTEGER     REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS shippers (
    shipper_id    SERIAL PRIMARY KEY,
    company_name  VARCHAR(80) NOT NULL,
    phone         VARCHAR(24)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      SERIAL PRIMARY KEY,
    customer_id   CHAR(5)        REFERENCES customers(customer_id),
    employee_id   INTEGER        REFERENCES employees(employee_id),
    order_date    DATE           NOT NULL,
    required_date DATE,
    shipped_date  DATE,
    ship_via      INTEGER        REFERENCES shippers(shipper_id),
    freight       NUMERIC(10, 2) NOT NULL DEFAULT 0,
    ship_country  VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS order_details (
    order_id    INTEGER        NOT NULL REFERENCES orders(order_id),
    product_id  INTEGER        NOT NULL REFERENCES products(product_id),
    unit_price  NUMERIC(10, 2) NOT NULL,
    quantity    SMALLINT       NOT NULL,
    discount    REAL           NOT NULL DEFAULT 0,
    PRIMARY KEY (order_id, product_id)
);

-- ── Data ──────────────────────────────────────────────────────────────────────

INSERT INTO categories (category_name, description) VALUES
  ('Beverages',       'Soft drinks, coffees, teas, beers, and ales'),
  ('Condiments',      'Sweet and savory sauces, relishes, spreads, and seasonings'),
  ('Confections',     'Desserts, candies, and sweet breads'),
  ('Dairy Products',  'Cheeses'),
  ('Grains/Cereals',  'Breads, crackers, pasta, and cereal'),
  ('Meat/Poultry',    'Prepared meats'),
  ('Produce',         'Dried fruit and bean curd'),
  ('Seafood',         'Seaweed and fish');

INSERT INTO suppliers (company_name, contact_name, contact_title, city, country, phone) VALUES
  ('Exotic Liquids',              'Charlotte Cooper',   'Purchasing Manager',  'London',       'UK',      '(171) 555-2222'),
  ('New Orleans Cajun Delights',  'Shelley Burke',      'Order Administrator', 'New Orleans',  'USA',     '(100) 555-4822'),
  ('Grandma Kellys Homestead',    'Regina Murphy',      'Sales Representative','Ann Arbor',    'USA',     '(313) 555-5735'),
  ('Tokyo Traders',               'Yoshi Nagase',       'Marketing Manager',   'Tokyo',        'Japan',   '(03) 3555-5011'),
  ('Cooperativa de Quesos',       'Antonio del Valle',  'Export Administrator','Oviedo',       'Spain',   '(98) 598 76 54'),
  ('Mayumis',                     'Mayumi Ohno',        'Marketing Rep.',      'Osaka',        'Japan',   '06-431-7877'),
  ('Pavlova Ltd.',                'Ian Devling',        'Marketing Manager',   'Melbourne',    'Australia','03-453-2428'),
  ('Specialty Biscuits Ltd.',     'Peter Wilson',       'Sales Rep.',          'Manchester',   'UK',      '(161) 555-4448'),
  ('PB Knäckebröd AB',           'Lars Peterson',      'Sales Agent',         'Göteborg',     'Sweden',  '031-987 65 43'),
  ('Refrescos Americanas',        'Carlos Diaz',        'Marketing Manager',   'Sao Paulo',    'Brazil',  '(11) 555 4640');

INSERT INTO products (product_name, supplier_id, category_id, unit_price, units_in_stock, units_on_order, reorder_level, discontinued) VALUES
  ('Chai',                      1, 1, 18.00,  39,  0, 10, FALSE),
  ('Chang',                     1, 1, 19.00,  17, 40, 25, FALSE),
  ('Aniseed Syrup',             1, 2, 10.00,  13, 70, 25, FALSE),
  ('Chef Antons Cajun Seasoning',2,2, 22.00,  53,  0,  0, FALSE),
  ('Chef Antons Gumbo Mix',     2, 2, 21.35,   0,  0,  0, TRUE),
  ('Grandmas Boysenberry Spread',3,2, 25.00,  120, 0, 25, FALSE),
  ('Uncle Bobs Organic Dried Pears',3,7,30.00,15,  0, 10, FALSE),
  ('Northwoods Cranberry Sauce',3, 2, 40.00,   6,  0,  0, FALSE),
  ('Mishi Kobe Niku',           4, 6, 97.00,  29,  0,  0, TRUE),
  ('Ikura',                     4, 8, 31.00,  31,  0,  0, FALSE),
  ('Queso Cabrales',            5, 4, 21.00,  22, 30, 30, FALSE),
  ('Queso Manchego La Pastora', 5, 4, 38.00,  86,  0,  0, FALSE),
  ('Konbu',                     6, 8,  6.00,  24,  0,  5, FALSE),
  ('Tofu',                      6, 7, 23.25,  35,  0,  0, FALSE),
  ('Genen Shouyu',              6, 2, 15.50,  39,  0,  5, FALSE),
  ('Pavlova',                   7, 3, 17.45,  29,  0, 10, FALSE),
  ('Alice Mutton',              7, 6, 39.00,   0,  0,  0, TRUE),
  ('Carnarvon Tigers',          7, 8, 62.50,  42,  0,  0, FALSE),
  ('Teatime Chocolate Biscuits',8, 3,  9.20,  25,  0,  5, FALSE),
  ('Sir Rodneys Marmalade',     8, 3, 81.00,  40,  0,  0, FALSE);

INSERT INTO customers VALUES
  ('ALFKI','Alfreds Futterkiste',      'Maria Anders',    'Sales Rep.',           'Berlin',      'Germany',  '030-0074321', 'maria@alfki.de'),
  ('ANATR','Ana Trujillo',             'Ana Trujillo',    'Owner',                'Mexico City', 'Mexico',   '(5) 555-4729','ana@anatr.mx'),
  ('ANTON','Antonio Moreno Taquería',  'Antonio Moreno',  'Owner',                'Mexico City', 'Mexico',   '(5) 555-3932','antonio@anton.mx'),
  ('AROUT','Around the Horn',          'Thomas Hardy',    'Sales Rep.',           'London',      'UK',       '(171) 555-7788','thomas@arout.co.uk'),
  ('BERGS','Berglunds snabbköp',       'Christina Berglund','Order Administrator','Luleå',       'Sweden',   '0921-12 34 65','christina@bergs.se'),
  ('BLAUS','Blauer See Delikatessen',  'Hanna Moos',      'Sales Rep.',           'Mannheim',    'Germany',  '0621-08460',  'hanna@blaus.de'),
  ('BLONP','Blondel père et fils',     'Frédérique Citeaux','Marketing Mgr.',     'Strasbourg',  'France',   '88.60.15.31', 'fred@blonp.fr'),
  ('BOLID','Bólido Comidas preparadas','Martín Sommer',   'Owner',                'Madrid',      'Spain',    '(91) 555 22 82','martin@bolid.es'),
  ('BONAP','Bon app',                  'Laurence Lebihan','Owner',                'Marseille',   'France',   '91.24.45.40', 'laurence@bonap.fr'),
  ('BOTTM','Bottom-Dollar Mkts',       'Elizabeth Lincoln','Accounting Mgr.',     'Tsawassen',   'Canada',   '(604) 555-4729','liz@bottm.ca'),
  ('BSBEV','B''s Beverages',            'Victoria Ashworth','Sales Rep.',          'London',      'UK',       '(171) 555-1212','victoria@bsbev.co.uk'),
  ('CACTU','Cactus Comidas para llevar','Patricio Simpson','Sales Agent',         'Buenos Aires','Argentina','(1) 135-5555', 'pat@cactu.ar'),
  ('CENTC','Centro comercial Moctezuma','Francisco Chang','Marketing Mgr.',       'Mexico City', 'Mexico',   '(5) 555-3392', 'fran@centc.mx'),
  ('CHOPS','Chop-suey Chinese',        'Yang Wang',       'Owner',                'Bern',        'Switzerland','0452-076545','yang@chops.ch'),
  ('COMMI','Comércio Mineiro',         'Pedro Afonso',    'Sales Assoc.',         'Sao Paulo',   'Brazil',   '(11) 555-7647','pedro@commi.br'),
  ('CONSH','Consolidated Holdings',    'Elizabeth Brown', 'Sales Rep.',           'London',      'UK',       '(171) 555-2282','liz@consh.co.uk'),
  ('DRACD','Drachenblut Delikatessen', 'Sven Ottlieb',    'Order Administrator', 'Aachen',      'Germany',  '0241-039123', 'sven@dracd.de'),
  ('DUMON','Du monde entier',          'Janine Labrune',  'Owner',                'Nantes',      'France',   '40.67.88.88', 'janine@dumon.fr'),
  ('EASTC','Eastern Connection',       'Ann Devon',       'Sales Agent',          'London',      'UK',       '(171) 555-0297','ann@eastc.co.uk'),
  ('ERNSH','Ernst Handel',             'Roland Mendel',   'Sales Mgr.',           'Graz',        'Austria',  '7675-3425',   'roland@ernsh.at'),
  ('FOLKO','Folk och fä HB',           'Maria Larsson',   'Owner',                'Bräcke',      'Sweden',   '0695-34 67 21','maria@folko.se'),
  ('HANAR','Hanari Carnes',            'Mario Pontes',    'Acct. Rep.',           'Rio de Janeiro','Brazil', '(21) 555-0091','mario@hanar.br'),
  ('HILAA','HILARION-Abastos',         'Carlos Hernández','Sales Rep.',           'San Cristóbal','Venezuela','(5) 555-1340','carlos@hilaa.ve'),
  ('ISLAT','Island Trading',           'Helen Bennett',   'Marketing Manager',    'Cowes',       'UK',       '(198) 555-8888','helen@islat.co.uk'),
  ('OTTIK','Ottilies Käseladen',       'Henriette Pfalzheim','Owner',             'Köln',        'Germany',  '0221-0644327','henriette@ottik.de'),
  ('QUEDE','Que Delícia',              'Bernardo Batista','Acct. Rep.',           'Rio de Janeiro','Brazil', '(21) 555-4252','bernardo@quede.br'),
  ('RATTC','Rattlesnake Canyon Grocery','Paula Wilson',   'Asst. Sales Agent',    'Albuquerque', 'USA',      '(505) 555-5939','paula@rattc.com'),
  ('RICSU','Richter Supermarkt',       'Michael Holz',    'Sales Mgr.',           'Genève',      'Switzerland','0897-034214','michael@ricsu.ch'),
  ('SUPRD','Suprêmes délices',         'Pascale Cartrain','Accounting Mgr.',      'Charleroi',   'Belgium',  '(071) 23 67 22 20','pascale@suprd.be'),
  ('TOMSP','Toms Spezialitäten',       'Karin Josephs',   'Marketing Manager',    'Münster',     'Germany',  '0251-031259','karin@tomsp.de'),
  ('VICTE','Victuailles en stock',     'Mary Saveley',    'Sales Agent',          'Lyon',        'France',   '78.32.54.86', 'mary@victe.fr'),
  ('VINET','Vins et alcools Chevalier','Paul Henriot',    'Acct. Manager',        'Reims',       'France',   '26.47.15.10', 'paul@vinet.fr'),
  ('WARTH','Wartian Herkku',           'Pirkko Koskitalo','Acct. Manager',        'Oulu',        'Finland',  '981-443655',  'pirkko@warth.fi'),
  ('WELLI','Wellington Importadora',   'Paula Parente',   'Sales Mgr.',           'Resende',     'Brazil',   '(14) 555-8122','paula@welli.br');

INSERT INTO employees (last_name, first_name, title, hire_date, city, country, reports_to) VALUES
  ('Davolio',   'Nancy',   'Sales Rep.',                     '1992-05-01', 'Seattle',   'USA', NULL),
  ('Fuller',    'Andrew',  'Vice President, Sales',          '1992-08-14', 'Tacoma',    'USA', NULL),
  ('Leverling', 'Janet',   'Sales Rep.',                     '1992-04-01', 'Kirkland',  'USA', 2),
  ('Peacock',   'Margaret','Sales Rep.',                     '1993-05-03', 'Redmond',   'USA', 2),
  ('Buchanan',  'Steven',  'Sales Manager',                  '1993-10-17', 'London',    'UK',  2),
  ('Suyama',    'Michael', 'Sales Rep.',                     '1993-10-17', 'London',    'UK',  5),
  ('King',      'Robert',  'Sales Rep.',                     '1994-01-02', 'London',    'UK',  5),
  ('Callahan',  'Laura',   'Inside Sales Coordinator',       '1994-03-05', 'Seattle',   'USA', 2),
  ('Dodsworth', 'Anne',    'Sales Rep.',                     '1994-11-15', 'London',    'UK',  5);

INSERT INTO shippers (company_name, phone) VALUES
  ('Speedy Express',  '(503) 555-9831'),
  ('United Package',  '(503) 555-3199'),
  ('Federal Shipping','(503) 555-9931');

INSERT INTO orders (customer_id, employee_id, order_date, required_date, shipped_date, ship_via, freight, ship_country) VALUES
  ('VINET', NULL,  '2024-07-04', '2024-08-01', '2024-07-16', 3, 32.38, 'France'),
  ('TOMSP', NULL,  '2024-07-05', '2024-08-16', '2024-07-10', 1, 11.61, 'Germany'),
  ('HANAR', NULL,  '2024-07-08', '2024-08-05', '2024-07-12', 2, 65.83, 'Brazil'),
  ('VICTE', NULL,  '2024-07-08', '2024-08-05', '2024-07-15', 1, 41.34, 'France'),
  ('SUPRD', NULL,  '2024-07-09', '2024-08-06', '2024-07-11', 2, 51.30, 'Belgium'),
  ('HANAR', NULL,  '2024-07-10', '2024-07-24', '2024-07-16', 2, 58.17, 'Brazil'),
  ('CHOPS', NULL,  '2024-07-11', '2024-08-08', '2024-07-23', 2, 22.98, 'Switzerland'),
  ('RICSU', NULL,  '2024-07-12', '2024-08-09', '2024-07-15', 3,148.33, 'Switzerland'),
  ('WELLI', NULL,  '2024-07-15', '2024-08-12', '2024-07-17', 2, 13.97, 'Brazil'),
  ('HILAA', NULL,  '2024-07-16', '2024-08-13', '2024-07-24', 2, 81.91, 'Venezuela'),
  ('ERNSH', NULL,  '2024-07-17', '2024-08-14', '2024-07-23', 1, 140.51,'Austria'),
  ('CENTC', NULL,  '2024-07-18', '2024-08-15', '2024-07-25', 3,  3.25, 'Mexico'),
  ('OTTIK', NULL,  '2024-07-19', '2024-08-16', '2024-07-29', 1, 55.09, 'Germany'),
  ('QUEDE', NULL,  '2024-07-22', '2024-08-19', '2024-07-30', 2, 3.05,  'Brazil'),
  ('RATTC', NULL,  '2024-07-23', '2024-08-20', '2024-07-31', 3, 48.29, 'USA'),
  ('ERNSH', NULL,  '2024-07-24', '2024-08-21', '2024-08-07', 2, 146.06,'Austria'),
  ('FOLKO', NULL,  '2024-07-25', '2024-08-22', '2024-08-12', 1,  3.67, 'Sweden'),
  ('BLONP', NULL,  '2024-07-26', '2024-09-23', '2024-07-31', 2, 55.28, 'France'),
  ('WARTH', NULL,  '2024-07-29', '2024-08-26', '2024-08-09', 3, 25.73, 'Germany'),
  ('ISLAT', NULL,  '2024-07-30', '2024-08-27', '2024-08-06', 3, 0.12,  'UK'),
  ('RATTC', NULL,  '2024-07-31', '2024-08-28', '2024-08-09', 3, 12.69, 'USA'),
  ('ERNSH', NULL,  '2024-08-01', '2024-08-29', '2024-08-02', 1, 70.39, 'Austria'),
  ('FOLKO', NULL,  '2024-08-02', '2024-08-30', '2024-08-12', 2,  1.35, 'Sweden'),
  ('AROUT', NULL,  '2024-08-05', '2024-09-02', '2024-08-26', 3, 13.55, 'UK'),
  ('BERGS', NULL,  '2024-08-06', '2024-09-03', '2024-08-07', 2,  0.00, 'Sweden'),
  ('ALFKI', NULL,  '2024-08-07', '2024-09-04', '2024-08-15', 1, 29.46, 'Germany'),
  ('ANATR', NULL,  '2024-08-08', '2024-09-05', '2024-08-14', 3,  3.67, 'Mexico'),
  ('ANTON', NULL,  '2024-08-09', '2024-09-06', '2024-08-14', 2, 23.79, 'Mexico'),
  ('AROUT', NULL,  '2024-08-12', '2024-09-09', '2024-08-19', 3, 57.15, 'UK'),
  ('BERGS', NULL,  '2024-08-13', '2024-09-10', '2024-08-14', 3, 76.07, 'Sweden');

-- Update employee_id to spread orders across employees
UPDATE orders SET employee_id = (order_id % 9) + 1;

-- All product_id values reference products 1-20 defined above.
INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount) VALUES
  (1,  11, 21.00, 12, 0.00),
  (1,   2, 19.00, 10, 0.00),
  (1,  12, 38.00,  5, 0.00),
  (2,  14, 23.25,  9, 0.00),
  (2,   1, 18.00, 40, 0.05),
  (3,   3, 10.00, 10, 0.00),
  (3,   2, 19.00, 35, 0.15),
  (3,   5, 21.35, 15, 0.15),
  (4,   6, 25.00,  6, 0.05),
  (4,   7, 30.00, 15, 0.05),
  (5,  17, 39.00, 20, 0.05),
  (5,  12, 38.00, 42, 0.05),
  (6,  13,  6.00, 15, 0.25),
  (7,   6, 25.00,  6, 0.15),
  (7,   4, 22.00, 15, 0.15),
  (8,  10, 31.00, 40, 0.10),
  (8,  11, 21.00, 20, 0.10),
  (9,   4, 22.00, 15, 0.15),
  (9,   9, 97.00,  6, 0.00),
  (10,  8, 40.00, 20, 0.00),
  (10, 16, 17.45, 15, 0.05),
  (11, 12, 38.00, 20, 0.00),
  (11, 10, 31.00, 40, 0.05),
  (12,  1, 18.00, 25, 0.00),
  (13, 11, 21.00, 10, 0.00),
  (13, 16, 17.45, 20, 0.00),
  (14,  2, 19.00, 12, 0.00),
  (14,  6, 25.00, 10, 0.00),
  (15, 12, 38.00,  5, 0.20),
  (15,  7, 30.00, 10, 0.10),
  (16, 17, 39.00, 30, 0.10),
  (16, 10, 31.00, 20, 0.00),
  (17,  7, 30.00, 20, 0.05),
  (17,  5, 21.35, 15, 0.05),
  (18, 10, 31.00, 40, 0.05),
  (18, 12, 38.00, 20, 0.00),
  (19, 19,  9.20,  6, 0.05),
  (19,  4, 22.00, 30, 0.05),
  (20,  6, 25.00, 20, 0.00),
  (20, 12, 38.00, 10, 0.00),
  (21,  8, 40.00, 30, 0.00),
  (21, 12, 38.00, 40, 0.05),
  (22, 19,  9.20, 30, 0.05),
  (22, 11, 21.00, 15, 0.05),
  (23, 16, 17.45, 10, 0.05),
  (23,  8, 40.00, 18, 0.10),
  (24,  1, 18.00,  6, 0.00),
  (24, 16, 17.45, 10, 0.05),
  (25, 12, 38.00, 20, 0.10),
  (26,  1, 18.00,  2, 0.10),
  (26, 12, 38.00, 12, 0.10),
  (27,  6, 25.00, 24, 0.10),
  (27, 16, 17.45, 20, 0.00),
  (28, 12, 38.00, 30, 0.10),
  (28, 16, 17.45, 15, 0.00),
  (29, 12, 38.00, 40, 0.10),
  (29, 16, 17.45, 25, 0.00),
  (30,  8, 40.00, 30, 0.00),
  (30, 12, 38.00, 24, 0.05);

-- ── Read-only role setup ────────────────────────────────────────────────────
-- The backend connects as the 'speakql' user defined in docker-compose.
-- In production, create a dedicated read-only role (see db/seed/create_readonly_role.sql).
