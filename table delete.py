import sqlite3

# connect to the database
conn = sqlite3.connect('organic_farming.db')
cursor = conn.cursor()

# delete the orders table
cursor.execute("DELETE FROM cart WHERE cart_product_id = 26")


# commit the changes and close the connection
conn.commit()
conn.close()