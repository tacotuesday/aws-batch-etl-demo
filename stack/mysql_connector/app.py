import sys
import logging
import pymysql
import json

# rds settings to replace with outputs from your RDS stack:
rds_host = "mysqldb.cncs44o8wyqo.us-east-1.rds.amazonaws.com"
user_name = "root"
password = "82cebeB6w1t9IiSeJaqT"
db_name = "myschema"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(
        host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5
    )

except pymysql.MySQLError as e:
    logger.error(
        "ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")


def lambda_handler(event, context):
    """
    This function creates a new RDS database table and writes records to it
    """
    try:
        message = event["Records"][0]["body"]
    except:
        message = '{\n     "registration_date": "2023-01-01;",\n     "user": "mshakhomirov"\n}'

    # Initialize item_count
    item_count = 0

    data = json.loads(message)
    user_id = data["user"]
    dt = data["registration_date"]

    sql_string = f"insert into user (id, registration_date) values({user_id}, '{dt}')"
    with conn.cursor() as cur:
        cur.execute("create schema if not exists myschema;")
        cur.execute(
            "create table if not exists myschema.users as select 1 as id, current_date() as registration_date union all select 2 as id, date_sub(current_date(), interval 1 day)  as registration_date;"
        )
        cur.execute(
            "create table if not exists myschema.transactions as select 1 as transaction_id, 1 as user_id, 10.99 as total_cost, current_date() as dt union all select 2 as transaction_id, 2 as user_id, 4.99 as total_cost, current_date() as dt union all select 3 as transaction_id, 2 as user_id, 4.99 as total_cost, date_sub(current_date(), interval 3 day) as dt union all select 4 as transaction_id, 1 as user_id, 4.99 as total_cost, date_sub(current_date(), interval 3 day) as dt union all select 5 as transaction_id, 1 as user_id, 5.99 as total_cost, date_sub(current_date(), interval 2 day) as dt union all select 6 as transaction_id, 1 as user_id, 15.99 as total_cost, date_sub(current_date(), interval 1 day) as dt union all select 7 as transaction_id, 1 as user_id, 55.99 as total_cost, date_sub(current_date(), interval 4 day) as dt ;"
        )
        cur.execute(
            "SELECT * FROM myschema.transactions INTO OUTFILE S3 's3://tacotuesday-s3-bucket/data/myschema/transactions/transactions.scv' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' OVERWRITE ON;"
        )
        cur.execute(
            "SELECT * FROM myschema.users INTO OUTFILE S3 's3://tacotuesday-s3-bucket/data/myschema/users/users.csv' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' OVERWRITE ON;"
        )
        cur.execute("show tables;")
        conn.commit()
        logger.info("Successfully connected and found tables in the database:")
        for row in cur:
            item_count += 1
            logger.info(row)
        return f"Found {item_count} items in RDS MySQL database"
        conn.commit()
    conn.commit()
