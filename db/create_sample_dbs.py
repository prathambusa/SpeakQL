"""
Creates two SQLite databases:
  financial.db  — stocks, prices, earnings, dividends, analyst ratings
  superstore.db — customers, products, orders, order_details with US geo data
"""
import sqlite3, random, math, os
from datetime import date, timedelta

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "sample_dbs")
os.makedirs(OUT, exist_ok=True)

# ─── helpers ──────────────────────────────────────────────────────────────────

def db(name):
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        os.remove(path)
    return sqlite3.connect(path)

def daterange(start, days):
    return [start + timedelta(d) for d in range(days)]

# ══════════════════════════════════════════════════════════════════════════════
# FINANCIAL DATABASE
# ══════════════════════════════════════════════════════════════════════════════
COMPANIES = [
    ("AAPL","Apple Inc","Technology","Consumer Electronics",182.50),
    ("MSFT","Microsoft Corp","Technology","Software",415.20),
    ("GOOGL","Alphabet Inc","Technology","Internet Services",175.80),
    ("AMZN","Amazon.com Inc","Consumer Discretionary","E-Commerce",195.60),
    ("NVDA","NVIDIA Corp","Technology","Semiconductors",875.40),
    ("META","Meta Platforms","Technology","Social Media",505.30),
    ("TSLA","Tesla Inc","Consumer Discretionary","Electric Vehicles",175.20),
    ("BRK","Berkshire Hathaway","Financials","Diversified",605.00),
    ("JPM","JPMorgan Chase","Financials","Banking",198.50),
    ("V","Visa Inc","Financials","Payments",278.90),
    ("JNJ","Johnson & Johnson","Healthcare","Pharmaceuticals",152.30),
    ("WMT","Walmart Inc","Consumer Staples","Retail",68.40),
    ("MA","Mastercard Inc","Financials","Payments",468.70),
    ("PG","Procter & Gamble","Consumer Staples","Household Products",162.10),
    ("HD","Home Depot","Consumer Discretionary","Home Improvement",358.20),
    ("CVX","Chevron Corp","Energy","Oil & Gas",154.60),
    ("MRK","Merck & Co","Healthcare","Pharmaceuticals",126.80),
    ("ABBV","AbbVie Inc","Healthcare","Biotechnology",172.40),
    ("PEP","PepsiCo Inc","Consumer Staples","Beverages",164.90),
    ("KO","Coca-Cola Co","Consumer Staples","Beverages",60.20),
    ("BAC","Bank of America","Financials","Banking",38.50),
    ("COST","Costco Wholesale","Consumer Staples","Retail",742.10),
    ("AVGO","Broadcom Inc","Technology","Semiconductors",1350.80),
    ("TMO","Thermo Fisher","Healthcare","Medical Devices",558.30),
    ("MCD","McDonald's Corp","Consumer Discretionary","Restaurants",284.60),
    ("CSCO","Cisco Systems","Technology","Networking",50.40),
    ("ABT","Abbott Laboratories","Healthcare","Medical Devices",106.20),
    ("ORCL","Oracle Corp","Technology","Enterprise Software",128.50),
    ("ACN","Accenture","Technology","IT Services",342.70),
    ("DIS","Walt Disney Co","Communication Services","Entertainment",95.30),
    ("ADBE","Adobe Inc","Technology","Software",560.40),
    ("NKE","Nike Inc","Consumer Discretionary","Apparel",98.60),
    ("NFLX","Netflix Inc","Communication Services","Streaming",645.20),
    ("CRM","Salesforce Inc","Technology","Cloud Software",285.40),
    ("LIN","Linde plc","Materials","Industrial Gases",448.30),
    ("TXN","Texas Instruments","Technology","Semiconductors",168.90),
    ("PM","Philip Morris","Consumer Staples","Tobacco",96.70),
    ("NEE","NextEra Energy","Utilities","Electric Utilities",58.30),
    ("RTX","Raytheon Technologies","Industrials","Aerospace",99.40),
    ("QCOM","Qualcomm Inc","Technology","Semiconductors",175.80),
    ("HON","Honeywell Intl","Industrials","Conglomerates",198.60),
    ("UPS","United Parcel Service","Industrials","Logistics",142.30),
    ("LOW","Lowe's Companies","Consumer Discretionary","Home Improvement",238.50),
    ("AMGN","Amgen Inc","Healthcare","Biotechnology",285.40),
    ("IBM","IBM Corp","Technology","Enterprise IT",185.60),
    ("GS","Goldman Sachs","Financials","Investment Banking",462.30),
    ("CAT","Caterpillar Inc","Industrials","Heavy Equipment",342.80),
    ("SPGI","S&P Global","Financials","Financial Data",445.20),
    ("AXP","American Express","Financials","Payments",226.40),
    ("MS","Morgan Stanley","Financials","Investment Banking",102.80),
]

ANALYSTS = ["Goldman Sachs","Morgan Stanley","JPMorgan","Citi","BofA","Wells Fargo","UBS","Barclays","Deutsche Bank","Raymond James"]
RATINGS  = ["Strong Buy","Buy","Outperform","Hold","Underperform","Sell"]
RATING_W = [0.15, 0.30, 0.20, 0.20, 0.10, 0.05]

print("Building financial.db …")
con = db("financial.db")
cur = con.cursor()

cur.executescript("""
CREATE TABLE sectors (
    sector_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT
);
CREATE TABLE companies (
    ticker      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    sector      TEXT NOT NULL,
    industry    TEXT NOT NULL,
    market_cap_b REAL,
    ipo_year    INTEGER,
    exchange    TEXT DEFAULT 'NASDAQ'
);
CREATE TABLE stock_prices (
    price_id  INTEGER PRIMARY KEY,
    ticker    TEXT NOT NULL REFERENCES companies(ticker),
    trade_date TEXT NOT NULL,
    open_price REAL, high_price REAL, low_price REAL,
    close_price REAL NOT NULL, volume INTEGER,
    UNIQUE(ticker, trade_date)
);
CREATE TABLE quarterly_earnings (
    id         INTEGER PRIMARY KEY,
    ticker     TEXT NOT NULL REFERENCES companies(ticker),
    year       INTEGER NOT NULL,
    quarter    INTEGER NOT NULL,
    revenue_m  REAL,
    net_income_m REAL,
    eps        REAL,
    eps_estimate REAL,
    UNIQUE(ticker, year, quarter)
);
CREATE TABLE dividends (
    id         INTEGER PRIMARY KEY,
    ticker     TEXT NOT NULL REFERENCES companies(ticker),
    ex_date    TEXT NOT NULL,
    amount     REAL NOT NULL,
    frequency  TEXT DEFAULT 'quarterly'
);
CREATE TABLE analyst_ratings (
    id         INTEGER PRIMARY KEY,
    ticker     TEXT NOT NULL REFERENCES companies(ticker),
    analyst    TEXT NOT NULL,
    rating     TEXT NOT NULL,
    price_target REAL,
    rating_date TEXT NOT NULL
);
""")

# sectors
sectors = sorted({c[2] for c in COMPANIES})
for i, s in enumerate(sectors, 1):
    cur.execute("INSERT INTO sectors VALUES (?,?,?)", (i, s, f"{s} sector companies"))

# companies
for t,n,sec,ind,price in COMPANIES:
    mcap = round(price * random.uniform(1e9, 3e12) / 1e9, 1)
    ipo  = random.randint(1980, 2015)
    exch = random.choice(["NASDAQ","NYSE","NYSE","NYSE"])
    cur.execute("INSERT INTO companies VALUES (?,?,?,?,?,?,?)", (t,n,sec,ind,mcap,ipo,exch))

# stock_prices — 2 years of trading days (≈504 days)
start = date(2024, 1, 2)
all_dates = []
d = start
while len(all_dates) < 504:
    if d.weekday() < 5:
        all_dates.append(d)
    d += timedelta(1)

rows = []
for tick, _, _, _, base_price in COMPANIES:
    price = base_price
    for td in all_dates:
        daily_ret = random.gauss(0.0003, 0.018)
        price = max(price * (1 + daily_ret), 1.0)
        hi = price * random.uniform(1.001, 1.025)
        lo = price * random.uniform(0.975, 0.999)
        op = random.uniform(lo, hi)
        vol = int(random.lognormvariate(math.log(5e6), 1.2))
        rows.append((tick, td.isoformat(), round(op,2), round(hi,2), round(lo,2), round(price,2), vol))
cur.executemany("INSERT INTO stock_prices(ticker,trade_date,open_price,high_price,low_price,close_price,volume) VALUES (?,?,?,?,?,?,?)", rows)

# quarterly_earnings — 8 quarters
rows = []
for tick, _, _, _, base_price in COMPANIES:
    rev = random.uniform(500, 80000)
    for yr in [2023, 2024]:
        for q in [1, 2, 3, 4]:
            rev_q = rev * random.uniform(0.85, 1.20)
            ni    = rev_q * random.uniform(0.05, 0.30)
            shares = random.uniform(500, 15000)
            eps    = round(ni / shares, 2)
            est    = round(eps * random.uniform(0.90, 1.10), 2)
            rows.append((tick, yr, q, round(rev_q,1), round(ni,1), eps, est))
cur.executemany("INSERT INTO quarterly_earnings(ticker,year,quarter,revenue_m,net_income_m,eps,eps_estimate) VALUES (?,?,?,?,?,?,?)", rows)

# dividends — only ~60% of companies pay dividends
rows = []
div_tickers = [t for t,*_ in COMPANIES if random.random() < 0.6]
div_dates = [date(2023,3,15), date(2023,6,15), date(2023,9,15), date(2023,12,15),
             date(2024,3,15), date(2024,6,15), date(2024,9,15), date(2024,12,15)]
for tick in div_tickers:
    amt = round(random.uniform(0.10, 1.50), 2)
    for dd in div_dates:
        rows.append((tick, dd.isoformat(), amt, "quarterly"))
cur.executemany("INSERT INTO dividends(ticker,ex_date,amount,frequency) VALUES (?,?,?,?)", rows)

# analyst_ratings
rows = []
for tick, *_ in COMPANIES:
    for _ in range(random.randint(3, 8)):
        analyst = random.choice(ANALYSTS)
        rating  = random.choices(RATINGS, RATING_W)[0]
        base    = dict(zip([t for t,*_ in COMPANIES], [p for *_,p in COMPANIES]))[tick]
        target  = round(base * random.uniform(0.80, 1.40), 2)
        rdate   = (date(2024,1,1) + timedelta(days=random.randint(0, 500))).isoformat()
        rows.append((tick, analyst, rating, target, rdate))
cur.executemany("INSERT INTO analyst_ratings(ticker,analyst,rating,price_target,rating_date) VALUES (?,?,?,?,?)", rows)

con.commit()
con.close()
print(f"  financial.db done — {len(COMPANIES)} companies, {len(rows)} analyst ratings")


# ══════════════════════════════════════════════════════════════════════════════
# SUPERSTORE DATABASE  (retail + geo)
# ══════════════════════════════════════════════════════════════════════════════
US_CITIES = [
    ("New York","NY","East","Northeast",40.71,-74.01),
    ("Los Angeles","CA","West","West",34.05,-118.24),
    ("Chicago","IL","Central","Midwest",41.88,-87.63),
    ("Houston","TX","South","South",29.76,-95.37),
    ("Phoenix","AZ","West","West",33.45,-112.07),
    ("Philadelphia","PA","East","Northeast",39.95,-75.17),
    ("San Antonio","TX","South","South",29.42,-98.49),
    ("San Diego","CA","West","West",32.72,-117.16),
    ("Dallas","TX","South","South",32.78,-96.80),
    ("San Jose","CA","West","West",37.34,-121.89),
    ("Austin","TX","South","South",30.27,-97.74),
    ("Jacksonville","FL","South","South",30.33,-81.66),
    ("Fort Worth","TX","South","South",32.75,-97.33),
    ("Columbus","OH","Central","Midwest",39.96,-82.99),
    ("Charlotte","NC","East","Southeast",35.23,-80.84),
    ("Indianapolis","IN","Central","Midwest",39.77,-86.16),
    ("San Francisco","CA","West","West",37.77,-122.42),
    ("Seattle","WA","West","West",47.61,-122.33),
    ("Denver","CO","West","West",39.74,-104.98),
    ("Nashville","TN","South","Southeast",36.17,-86.78),
    ("Oklahoma City","OK","South","South",35.47,-97.52),
    ("El Paso","TX","South","South",31.76,-106.49),
    ("Washington","DC","East","Northeast",38.91,-77.04),
    ("Boston","MA","East","Northeast",42.36,-71.06),
    ("Louisville","KY","Central","Southeast",38.25,-85.76),
    ("Portland","OR","West","West",45.52,-122.68),
    ("Las Vegas","NV","West","West",36.17,-115.14),
    ("Memphis","TN","South","Southeast",35.15,-90.05),
    ("Atlanta","GA","South","Southeast",33.75,-84.39),
    ("Minneapolis","MN","Central","Midwest",44.98,-93.27),
    ("Tucson","AZ","West","West",32.22,-110.97),
    ("Fresno","CA","West","West",36.74,-119.77),
    ("Sacramento","CA","West","West",38.58,-121.49),
    ("Kansas City","MO","Central","Midwest",39.10,-94.58),
    ("Mesa","AZ","West","West",33.42,-111.74),
    ("Cleveland","OH","Central","Midwest",41.50,-81.69),
    ("Omaha","NE","Central","Midwest",41.26,-96.01),
    ("Raleigh","NC","East","Southeast",35.78,-78.64),
    ("Miami","FL","South","Southeast",25.77,-80.19),
    ("Tampa","FL","South","Southeast",27.95,-82.46),
]

PRODUCTS = [
    # (name, category, sub_category, unit_cost)
    ("Staple envelope","Office Supplies","Paper",4.20),
    ("Xerox 1967","Office Supplies","Paper",6.48),
    ("Easy-staple paper","Office Supplies","Paper",9.99),
    ("Avery Binder","Office Supplies","Binders",3.50),
    ("Cardinal Binder","Office Supplies","Binders",7.20),
    ("Acme scissors","Office Supplies","Art",3.99),
    ("Fiskars scissors","Office Supplies","Art",5.99),
    ("Stapler","Office Supplies","Fasteners",12.50),
    ("BIC pen 12-pk","Office Supplies","Pens",3.00),
    ("Sharpie markers","Office Supplies","Art",8.99),
    ("HP printer paper","Office Supplies","Paper",39.99),
    ("Post-it notes","Office Supplies","Paper",4.29),
    ("File folders","Office Supplies","Storage",12.99),
    ("Desk organizer","Office Supplies","Storage",18.50),
    ("Rubber bands","Office Supplies","Fasteners",1.99),
    ("Bush bookcase","Furniture","Bookcases",229.99),
    ("Sauder bookcase","Furniture","Bookcases",299.99),
    ("Atlantic bookcase","Furniture","Bookcases",189.99),
    ("HON chair","Furniture","Chairs",299.99),
    ("Steelcase chair","Furniture","Chairs",449.99),
    ("SAFCO chair","Furniture","Chairs",199.99),
    ("Ikea table","Furniture","Tables",129.99),
    ("Bretford table","Furniture","Tables",259.99),
    ("Bevis table","Furniture","Tables",189.99),
    ("Global Deluxe desk","Furniture","Furnishings",499.99),
    ("Eldon desk","Furniture","Furnishings",299.99),
    ("Hon 10700 desk","Furniture","Furnishings",649.99),
    ("Apple iPhone","Technology","Phones",999.00),
    ("Samsung Galaxy","Technology","Phones",799.00),
    ("Motorola phone","Technology","Phones",399.00),
    ("Apple iPad","Technology","Tablets",799.00),
    ("Amazon Kindle","Technology","Tablets",249.00),
    ("Samsung tablet","Technology","Tablets",549.00),
    ("HP laptop","Technology","Machines",849.00),
    ("Dell laptop","Technology","Machines",999.00),
    ("Lenovo laptop","Technology","Machines",749.00),
    ("Logitech keyboard","Technology","Accessories",79.99),
    ("Microsoft mouse","Technology","Accessories",29.99),
    ("HP monitor","Technology","Machines",349.99),
    ("Brother printer","Technology","Machines",199.99),
    ("Cisco router","Technology","Networking",149.99),
    ("APC UPS","Technology","Networking",89.99),
    ("SanDisk USB drive","Technology","Accessories",19.99),
    ("Seagate hard drive","Technology","Machines",89.99),
    ("LG external drive","Technology","Machines",59.99),
]

SEGMENTS   = ["Consumer","Corporate","Home Office"]
SHIP_MODES = ["Standard Class","Second Class","First Class","Same Day"]
SHIP_DAYS  = {"Standard Class":5,"Second Class":3,"First Class":2,"Same Day":0}

print("Building superstore.db …")
con = db("superstore.db")
cur = con.cursor()

cur.executescript("""
CREATE TABLE regions (
    region_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);
CREATE TABLE cities (
    city_id    INTEGER PRIMARY KEY,
    city       TEXT NOT NULL,
    state      TEXT NOT NULL,
    region     TEXT NOT NULL,
    sub_region TEXT,
    latitude   REAL,
    longitude  REAL
);
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    segment       TEXT NOT NULL,
    city          TEXT NOT NULL,
    state         TEXT NOT NULL,
    region        TEXT NOT NULL,
    postal_code   TEXT,
    latitude      REAL,
    longitude     REAL
);
CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,
    sub_category  TEXT NOT NULL,
    unit_cost     REAL NOT NULL
);
CREATE TABLE orders (
    order_id       TEXT PRIMARY KEY,
    order_date     TEXT NOT NULL,
    ship_date      TEXT NOT NULL,
    ship_mode      TEXT NOT NULL,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    city           TEXT,
    state          TEXT,
    region         TEXT,
    postal_code    TEXT
);
CREATE TABLE order_details (
    detail_id   INTEGER PRIMARY KEY,
    order_id    TEXT NOT NULL REFERENCES orders(order_id),
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    sales       REAL NOT NULL,
    quantity    INTEGER NOT NULL,
    discount    REAL NOT NULL DEFAULT 0,
    profit      REAL NOT NULL
);
CREATE TABLE returns (
    return_id  INTEGER PRIMARY KEY,
    order_id   TEXT NOT NULL REFERENCES orders(order_id),
    reason     TEXT,
    return_date TEXT
);
""")

# regions
for r in ["East","West","Central","South"]:
    cur.execute("INSERT INTO regions(name,description) VALUES (?,?)", (r, f"{r} region of the US"))

# cities
for i,(city,state,region,sub,lat,lon) in enumerate(US_CITIES, 1):
    cur.execute("INSERT INTO cities VALUES (?,?,?,?,?,?,?)", (i,city,state,region,sub,lat,lon))

# customers — 800 customers spread across cities
FIRST = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Barbara",
         "David","Susan","Richard","Jessica","Joseph","Sarah","Thomas","Karen","Charles","Lisa",
         "Emily","Matthew","Ashley","Joshua","Amanda","Daniel","Stephanie","Andrew","Melissa","Ryan"]
LAST  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore",
         "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Young","King"]
cust_rows = []
for i in range(1, 801):
    fn = random.choice(FIRST)
    ln = random.choice(LAST)
    seg= random.choice(SEGMENTS)
    city,state,region,_,lat,lon = random.choice(US_CITIES)
    pc = str(random.randint(10000, 99999))
    cust_rows.append((i, f"{fn} {ln}", seg, city, state, region, pc, lat, lon))
cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)", cust_rows)

# products
for i,(name,cat,sub,cost) in enumerate(PRODUCTS, 1):
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (i,name,cat,sub,cost))

# orders + details — 8000 orders
REASONS = ["Wrong item","Defective","Changed mind","Late delivery","Quality issue"]
order_rows, detail_rows, return_rows = [], [], []
detail_id = 1
return_id = 1
start_ord = date(2022, 1, 1)
for i in range(1, 8001):
    oid = f"ORD-{i:05d}"
    cid = random.randint(1, 800)
    cust = cust_rows[cid-1]
    odate = start_ord + timedelta(days=random.randint(0, 900))
    mode  = random.choices(SHIP_MODES, [0.60, 0.20, 0.15, 0.05])[0]
    sdate = odate + timedelta(days=SHIP_DAYS[mode] + random.randint(0,2))
    city,state,region = cust[3], cust[4], cust[5]
    pc = cust[6]
    order_rows.append((oid, odate.isoformat(), sdate.isoformat(), mode, cid, city, state, region, pc))

    n_items = random.choices([1,2,3,4,5], [0.4,0.3,0.15,0.10,0.05])[0]
    picked  = random.sample(range(1, len(PRODUCTS)+1), min(n_items, len(PRODUCTS)))
    for pid in picked:
        _,_,_,cost = PRODUCTS[pid-1]
        qty  = random.randint(1, 10)
        disc = random.choices([0, 0.1, 0.2, 0.3, 0.4], [0.5,0.2,0.15,0.10,0.05])[0]
        price= cost * random.uniform(1.10, 2.20)
        sales= round(price * qty * (1 - disc), 2)
        margin= random.uniform(-0.10, 0.40)
        profit= round(sales * margin, 2)
        detail_rows.append((detail_id, oid, pid, sales, qty, disc, profit))
        detail_id += 1

    # ~8% return rate
    if random.random() < 0.08:
        rdate = sdate + timedelta(days=random.randint(3, 30))
        return_rows.append((return_id, oid, random.choice(REASONS), rdate.isoformat()))
        return_id += 1

cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", order_rows)
cur.executemany("INSERT INTO order_details VALUES (?,?,?,?,?,?,?)", detail_rows)
cur.executemany("INSERT INTO returns VALUES (?,?,?,?)", return_rows)

con.commit()
con.close()
print(f"  superstore.db done — {len(order_rows)} orders, {len(detail_rows)} line items, {len(return_rows)} returns")
print("All done.")
