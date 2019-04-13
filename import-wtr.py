import csv
import re
import os
import sqlite3
import pint
import sys
import dateutil.parser

ureg = pint.UnitRegistry()

try:
    os.remove('wtr.db')
except:
    pass

conn = sqlite3.connect('wtr.db')
conn.enable_load_extension(True)

if sys.platform == 'darwin':
    conn.load_extension("/usr/local/lib/mod_spatialite.dylib")
elif sys.platform == 'linux':
    conn.load_extension("/usr/local/lib/mod_spatialite")
else:
    raise Exception("Unknown platform: {}".format(sys.platform))

c = conn.cursor()

c.execute("SELECT InitSpatialMetaData()")

c.execute("""CREATE TABLE licensee (
            id INTEGER PRIMARY KEY,
            name TEXT
          )""")

c.execute("""CREATE TABLE product (
            id INTEGER PRIMARY KEY,
            name TEXT
          )""")

c.execute("""CREATE TABLE license (
    id TEXT PRIMARY KEY,
    licensee INTEGER NOT NULL,
    product INTEGER,
    tradeable BOOLEAN,
    issued DATE,
    status TEXT,
    FOREIGN KEY (licensee) REFERENCES licensee(id),
    FOREIGN KEY (product) REFERENCES product(id)
    )
""")

c.execute("""CREATE TABLE license_frequency (
    id INTEGER PRIMARY KEY,
    license TEXT,
    tx_rx TEXT,
    frequency INT,
    channel_width INT,
    area TEXT,
    height NUMERIC,
    max_erp NUMERIC,
    antenna_type TEXT,
    gain NUMERIC,
    azimuth NUMERIC,
    code_h TEXT,
    code_v TEXT,
    antenna_height NUMERIC,
    antenna_location TEXT,
    efl_upper_lower TEXT,
    antenna_elevation TEXT,
    antenna_polarisation TEXT,
    antenna_name TEXT,
    feed_loss NUMERIC,
    fade_margin TEXT,
    emi_code TEXT,
    FOREIGN KEY (license) REFERENCES license(id)
    )
""")

c.execute("""SELECT AddGeometryColumn('license_frequency', 'Geometry', 4326, 'POINT', 'XY')""")

inserted_licenses = set()


def yesno(val):
    return val == 'Yes'


def parsedate(val):
    try:
        return dateutil.parser.parse(val)
    except ValueError:
        return None


def freq(val):
    if val == '':
        return None
    return ureg(val).to_base_units().magnitude


def insert_licensee(name):
    c.execute("SELECT id FROM licensee WHERE name = ?", (name,))
    res = c.fetchone()
    if res is None:
        c.execute("INSERT INTO licensee (name) VALUES (?)", (name,))
        return c.lastrowid
    return res[0]


def insert_product(name, product_id=None):
    if product_id:
        c.execute("SELECT id FROM product WHERE id = ?", (product_id,))
    else:
        c.execute("SELECT id FROM product WHERE name = ?", (name,))
    res = c.fetchone()
    if res is None:
        if product_id:
            c.execute("INSERT INTO product (id, name) VALUES (?, ?)", (product_id, name))
        else:
            c.execute("INSERT INTO product (name) VALUES (?)", (name,))
        return c.lastrowid
    return res[0]


def insert_license(line):
    if line[0] in inserted_licenses:
        return
    inserted_licenses.add(line[0])
    licensee = insert_licensee(line[1])
    match = re.match(r'^([0-9]+)[ \-](.*)$', line[2])
    product = insert_product(match.group(2), match.group(1))
    c.execute("""INSERT INTO license(id, licensee, product, tradeable, issued, status) VALUES
                                    (?, ?, ?, ?, ?, ?)""",
              (line[0], licensee, product, yesno(line[4]), parsedate(line[5]), line[6]))


def insert_light_license(line):
    licensee = insert_licensee(line[2])
    product = insert_product(line[3])
    try:
        c.execute("""INSERT INTO license(id, licensee, product, tradeable, issued, status)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (line[1], licensee, product, yesno(line[7]), parsedate(line[8]), line[4]))
    except sqlite3.IntegrityError as e:
        print("Error inserting license {} - {}".format(line, e))


def insert_frequency(line):
    if line[8] != '':
        location = 'GeomFromText("POINT(%s %s)", 4326)' % (line[8], line[7])
    else:
        location = 'NULL'
    c.execute("""INSERT INTO license_frequency(license, tx_rx, frequency, channel_width, height, max_erp,
                 antenna_type, gain, azimuth, code_h, code_v, antenna_height, antenna_location,
                 efl_upper_lower, antenna_elevation, antenna_polarisation, antenna_name, feed_loss,
                 fade_margin, emi_code, area, Geometry) VALUES
                 (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, %s)""" % location,
              (line[0], line[10], freq(line[11]), freq(line[12]), line[13],
               line[14], line[15], line[16], line[17], line[18],
               line[19], line[20], line[21], line[22], line[23],
               line[24], line[25], line[26], line[27], line[28],
               line[29]))


# 0 Published,Licence Number,Licensee,Licence Type,Status,
# 5 Surrender Date,Revocation Date,Tradable,Licence Issued Date, National Grid Reference

with open('data/register_light.csv') as f:
    reader = csv.reader(f)
    next(reader)
    for line in reader:
        insert_light_license(line)

conn.commit()

# 0 Lic No, Licensee, Product, Publish_Flag, Trade_Flag,
# 5 Issue Date, lic status, Latitiude, Longitude, NGR,
# 10 TX/Rx, Freq, Channel_Width, Height, Max Radiated Power ERP,
# 15 Antenna Type, Gain,Azimuth,An Code H,An Code V,
# 20 Antenna Height, Antenna Location, EFL_UPPER_LOWER, Ant Elevation, Ant Polarisation,
# 25 Antenna Name, Ant Feeding Loss, Fade Margin, EMI Code, Area Code/Country

with open('data/register.csv') as f:
    reader = csv.reader(f)
    next(reader)
    for line in reader:
        insert_license(line)
        insert_frequency(line)

conn.commit()

c.execute("CREATE VIRTUAL TABLE licensee_fts USING fts4(name, content=\"licensee\")")
c.execute("INSERT INTO licensee_fts (rowid, name) SELECT rowid, name FROM licensee")
c.execute("""CREATE VIRTUAL TABLE license_frequency_fts
             USING fts4(area, content="license_frequency")""")
c.execute("INSERT INTO license_frequency_fts (rowid, area) SELECT rowid, area FROM license_frequency")

conn.commit()
