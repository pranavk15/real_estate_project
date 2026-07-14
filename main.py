from flask import Flask, render_template, request, redirect, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os
import random
import uuid

app = Flask(__name__)
app.secret_key = 'Administrator'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '9526'
app.config['MYSQL_DB'] = 'realestate'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mysql = MySQL(app)


class HybridRow(dict):
    """Allows both row['column'] and old template row[0] access."""

    def __init__(self, row):
        super().__init__(row)
        self._keys = list(row.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            key = self._keys[key]
        return super().__getitem__(key)


def fetch_one(cursor):
    row = cursor.fetchone()
    return HybridRow(row) if row else None


def fetch_all(cursor):
    return [HybridRow(row) for row in cursor.fetchall()]


# ======================================================
# HOME
# ======================================================

@app.route('/')
def index():
    return render_template('index.html')


# ======================================================
# LOGIN PAGE
# ======================================================

@app.route('/login')
def login():
    return render_template('login.html')


# ======================================================
# ADMIN LOGIN
# ======================================================

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']

    if username == 'admin' and password == 'super':
        flash('Welcome Admin', 'success')
        return redirect('/admin/admin_dashboard')

    flash('Invalid Admin Credentials', 'error')
    return redirect('/login')


# ======================================================
# ADMIN DASHBOARD
# ======================================================

@app.route('/admin/admin_dashboard')
def admin_dashboard():
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT COUNT(*) AS total FROM agents')
    total_agents = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) AS total FROM banks')
    total_banks = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) AS total FROM properties')
    total_properties = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM properties
        WHERE status='Sold'
    """)
    sold_properties = cursor.fetchone()['total']

    cursor.execute("""
        SELECT
            properties.id,
            properties.property_name,
            properties.location,
            properties.minimum_price,
            properties.status,
            banks.bankname,
            properties.image,
            banks.logo
        FROM properties
        JOIN banks ON properties.bank_id = banks.id
        ORDER BY properties.id DESC
    """)
    recent_properties = fetch_all(cursor)
#notification

    cursor.close()

    return render_template(
        'admin/admin_dashboard.html',
        total_agents=total_agents,
        total_banks=total_banks,
        total_properties=total_properties,
        sold_properties=sold_properties,
        recent_properties=recent_properties,


    )


# ======================================================
# ADMIN ALL PROPERTIES
# ======================================================

@app.route('/admin/all_properties')
def all_properties():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            properties.id,
            properties.property_name,
            properties.location,
            properties.minimum_price,
            properties.status,
            banks.bankname,
            properties.image
        FROM properties
        JOIN banks ON properties.bank_id = banks.id
        ORDER BY properties.id DESC
    """)
    properties = fetch_all(cursor)

    cursor.close()

    return render_template(
        'admin/all_properties.html',
        properties=properties
    )


# ======================================================
# ADMIN ALL AGENTS
# ======================================================

@app.route('/admin/all_agents')
def all_agents():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM agents
        ORDER BY id DESC
    """)
    agents = fetch_all(cursor)

    cursor.close()

    return render_template(
        'admin/all_agents.html',
        agents=agents,
    )


# ======================================================
# ADMIN ALL BANKS
# ======================================================

@app.route('/admin/all_banks')
def all_banks():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM banks
        ORDER BY id DESC
    """)
    banks = fetch_all(cursor)

    cursor.close()

    return render_template(
        'admin/all_banks.html',
        banks=banks
    )


# ======================================================
# DELETE AGENT
# ======================================================

@app.route('/admin/delete_agent/<int:id>')
def delete_agent(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM agents
        WHERE id=%s
    """, (id,))

    mysql.connection.commit()
    cursor.close()

    return redirect('/admin/all_agents')


# ======================================================
# DELETE BANK
# ======================================================

@app.route('/admin/delete_bank/<int:id>')
def delete_bank(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM banks
        WHERE id=%s
    """, (id,))

    mysql.connection.commit()
    cursor.close()

    return redirect('/admin/all_banks')


# ======================================================
# DELETE PROPERTY
# ======================================================

@app.route('/admin/delete_property/<int:id>')
def delete_property(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM properties
        WHERE id=%s
    """, (id,))

    mysql.connection.commit()
    cursor.close()

    return redirect('/admin/all_properties')


# ======================================================
# AGENT REGISTER
# ======================================================

@app.route('/agent_register', methods=['POST'])
def agent_register():
    cursor = mysql.connection.cursor()

    fullname = request.form['fullname']
    agency = request.form['agency']
    email = request.form['email']
    phone = request.form['phone']
    gender = request.form['gender']
    password = request.form['password']
    address = request.form['address']

    profile = request.files.get('profile_image')

    if profile and profile.filename.strip() != '':
        filename = f"{uuid.uuid4().hex}_{secure_filename(profile.filename)}"
        profile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        profile_image = filename
    elif gender == 'Female':
        profile_image = 'female.jpg'
    else:
        profile_image = 'male.jpg'

    cursor.execute("""
        INSERT INTO agents
        (
            fullname,
            agency,
            email,
            phone,
            gender,
            password,
            address,
            profile_image
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        fullname,
        agency,
        email,
        phone,
        gender,
        password,
        address,
        profile_image
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect('/login')


# ======================================================
# PENDING OFFER
# ======================================================



# ======================================================
# BANK REGISTER
# ======================================================

@app.route('/bank_register', methods=['POST'])
def bank_register():
    cursor = mysql.connection.cursor()

    bankname = request.form['bankname']
    branch = request.form['branch']
    ifsc = request.form['ifsc']
    email = request.form['email']
    password = request.form['password']
    address = request.form['address']

    logo = request.files.get('logo')

    if logo and logo.filename.strip() != '':
        filename = secure_filename(logo.filename)
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        bank_logo = filename
    else:
        bank_logo = 'default-bank.jpg'

    cursor.execute("""
        INSERT INTO banks
        (
            bankname,
            branch,
            ifsc,
            email,
            password,
            address,
            logo
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        bankname,
        branch,
        ifsc,
        email,
        password,
        address,
        bank_logo
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect('/login')


# ======================================================
# UPDATE BANK PROFILE
# ======================================================

@app.route('/bank/update_profile/<int:bank_id>', methods=['POST'])
def update_bank_profile(bank_id):
    cursor = mysql.connection.cursor()

    bankname = request.form['bankname']
    branch = request.form['branch']
    ifsc = request.form['ifsc']
    email = request.form['email']
    address = request.form['address']

    cursor.execute("""
        SELECT logo
        FROM banks
        WHERE id=%s
    """, (bank_id,))

    bank = fetch_one(cursor)
    logo = bank['logo'] if bank else 'default-bank.jpg'

    new_logo = request.files.get('logo')

    if new_logo and new_logo.filename.strip() != '':
        filename = secure_filename(new_logo.filename)
        new_logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo = filename

    cursor.execute("""
        UPDATE banks
        SET
            bankname=%s,
            branch=%s,
            ifsc=%s,
            email=%s,
            address=%s,
            logo=%s
        WHERE id=%s
    """, (
        bankname,
        branch,
        ifsc,
        email,
        address,
        logo,
        bank_id
    ))

    mysql.connection.commit()
    cursor.close()
    flash("Property added successfully.", "success")
    return redirect(f'/bank/bank_dashboard/{bank_id}')


# ======================================================
# BANK PROFILE EDIT
# ======================================================

@app.route('/bank/edit_profile/<int:bank_id>')
def edit_bank_profile(bank_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM banks
        WHERE id=%s
    """, (bank_id,))

    bank = fetch_one(cursor)

    cursor.close()

    return render_template(
        "bank/edit_profile.html",
        bank=bank,
        bank_id=bank_id
    )

# ======================================================
# AGENT LOGIN
# ======================================================

@app.route('/agent_login', methods=['POST'])
def agent_login():
    cursor = mysql.connection.cursor()

    email = request.form['email']
    password = request.form['password']

    cursor.execute("""
        SELECT *
        FROM agents
        WHERE email=%s
        AND password=%s
    """, (email, password))
    result = fetch_one(cursor)

    cursor.close()

    if result:
        flash('Agent Login Successful', 'success')
        return redirect(f"/agent/agent_dashboard/{result['id']}")

    flash('Invalid Email or Password', 'error')
    return redirect('/login')


# ======================================================
# BANK LOGIN
# ======================================================

@app.route('/bank_login', methods=['POST'])
def bank_login():
    cursor = mysql.connection.cursor()

    email = request.form['email']
    password = request.form['password']

    cursor.execute("""
        SELECT *
        FROM banks
        WHERE email=%s
        AND password=%s
    """, (email, password))
    result = fetch_one(cursor)

    cursor.close()

    if result:
        flash('Bank Login Successful', 'success')
        return redirect(f"/bank/bank_dashboard/{result['id']}")

    flash('Invalid Email or Password', 'error')
    return redirect('/login')


# ======================================================
# BANK DASHBOARD
# ======================================================

@app.route('/bank/bank_dashboard/<int:bank_id>')
def bank_dashboard(bank_id):

    reset_expired_pending_properties()

    cursor = mysql.connection.cursor()

    # Bank Details
    cursor.execute("""
        SELECT *
        FROM banks
        WHERE id=%s
    """, (bank_id,))
    bank = fetch_one(cursor)

    # All Properties
    cursor.execute("""
        SELECT *
        FROM properties
        WHERE bank_id=%s
        ORDER BY id DESC
    """, (bank_id,))
    properties = fetch_all(cursor)

    # notification
    cursor.execute("""
    SELECT *
    FROM notifications
    WHERE receiver_type='bank'
    AND receiver_id=%s
    AND is_read=0
    ORDER BY id DESC
    """, (bank_id,))

    notifications = fetch_all(cursor)

    # Dashboard Statistics (ONE QUERY)
    cursor.execute("""
        SELECT
            COUNT(*) AS total_properties,
            SUM(status='Available') AS available_properties,
            SUM(status='Pending') AS pending_properties,
            SUM(status='Sold') AS sold_properties,
            (
                SELECT COUNT(*)
                FROM property_offers po
                JOIN properties p
                    ON po.property_id = p.id
                WHERE p.bank_id = %s
            ) AS total_offers
        FROM properties
        WHERE bank_id = %s
    """, (bank_id, bank_id))

    stats = cursor.fetchone()

    total_properties = stats['total_properties']
    available_properties = stats['available_properties'] or 0
    pending_properties = stats['pending_properties'] or 0
    sold_properties = stats['sold_properties'] or 0
    total_offers = stats['total_offers']

    cursor.close()

    return render_template(
        'bank/bank_dashboard.html',
        bank=bank,
        bank_id=bank_id,
        properties=properties,
        total_properties=total_properties,
        available_properties=available_properties,
        pending_properties=pending_properties,
        sold_properties=sold_properties,
        total_offers=total_offers,
        notifications=notifications
    )

# ======================================================
# ADD PROPERTY
# ======================================================

@app.route('/bank/add_property/<int:bank_id>', methods=['POST'])
def add_property(bank_id):

    cursor = mysql.connection.cursor()

    property_name = request.form['property_name']
    location = request.form['location']
    map_link = request.form['map_link']
    minimum_price = int(request.form['minimum_price'])

    images = [
        image for image in request.files.getlist('images')
        if image.filename.strip() != ''
    ]

    if len(images) < 2:
        cursor.close()
        flash("Please upload at least 2 images.", "danger")
        return redirect(f"/bank/properties/{bank_id}")

    filenames = []

    for image in images:
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filenames.append(filename)

    image_string = ",".join(filenames)

    cursor.execute("""
        INSERT INTO properties
        (
            bank_id,
            property_name,
            location,
            map_link,
            minimum_price,
            image
        )
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        bank_id,
        property_name,
        location,
        map_link,
        minimum_price,
        image_string
    ))

    mysql.connection.commit()
# notification
    cursor.execute("""
    INSERT INTO notifications
    (receiver_type,receiver_id,title,message,icon)
    VALUES(%s,%s,%s,%s,%s)
    """, (
        'admin',
        1,
        'New Property',
        f'{property_name} was added.',
        'fa-house'
    ))


    mysql.connection.commit()
    cursor.close()

    flash("Property added successfully!", "success")

    return redirect(f"/bank/properties/{bank_id}")

# ======================================================
# UPDATE PROPERTY PAGE
# ======================================================

@app.route('/bank/update_property/<int:id>')
def update_property(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM properties
        WHERE id=%s
    """, (id,))
    property = fetch_one(cursor)

    cursor.close()

    return render_template(
        'bank/update_property.html',
        property=property
    )


# AGENT PROFILE EDIT


@app.route('/agent/edit_profile/<int:agent_id>')
def edit_profile(agent_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM agents
        WHERE id=%s
    """, (agent_id,))

    agent = fetch_one(cursor)

    cursor.close()

    return render_template(
        "agent/edit_profile.html",
        agent=agent,
        agent_id=agent_id
    )



# LOGOUT


@app.route('/logout')
def logout():
    return redirect('/login')



# SAVE UPDATED PROPERTY


@app.route('/bank/save_updated_property/<int:id>', methods=['POST'])
def save_updated_property(id):

    cursor = mysql.connection.cursor()

    property_name = request.form['property_name']
    location = request.form['location']
    map_link = request.form['map_link']
    minimum_price = int(request.form['minimum_price'])

    cursor.execute("""
        SELECT bank_id,image
        FROM properties
        WHERE id=%s
    """, (id,))

    property_data = fetch_one(cursor)

    if not property_data:
        cursor.close()
        return "Property not found"

    bank_id = property_data['bank_id']
    image_string = property_data['image']

    valid_images = [
        image for image in request.files.getlist('images')
        if image.filename.strip() != ''
    ]

    if valid_images:

        filenames = []

        for image in valid_images:

            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)

        image_string = ",".join(filenames)

    cursor.execute("""
        UPDATE properties
        SET
            property_name=%s,
            location=%s,
            map_link=%s,
            minimum_price=%s,
            image=%s
        WHERE id=%s
    """, (
        property_name,
        location,
        map_link,
        minimum_price,
        image_string,
        id
    ))

    mysql.connection.commit()
    cursor.close()

    flash("Property updated successfully!", "success")

    return redirect(f"/bank/properties/{bank_id}")


# VIEW AGENT


@app.route('/admin/view_agent/<int:id>')
def view_agent(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM agents
        WHERE id=%s
    """, (id,))
    agent = fetch_one(cursor)

    cursor.close()

    return render_template(
        'agent/view_agent.html',
        agent=agent
    )



# VIEW BANK


@app.route('/admin/view_bank/<int:id>')
def view_bank(id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM banks
        WHERE id=%s
    """, (id,))
    bank = fetch_one(cursor)

    cursor.close()

    return render_template(
        'bank/view_bank.html',
        bank=bank
    )
# AGENT DASHBOARD

@app.route('/agent/agent_dashboard/<int:agent_id>')
def agent_dashboard(agent_id):
    # Automatically reset expired pending properties
    reset_expired_pending_properties()
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            property_offers.*,
            properties.property_name
        FROM property_offers
        JOIN properties
        ON property_offers.property_id = properties.id
      WHERE property_offers.agent_id=%s
AND property_offers.status='Accepted'
AND property_offers.payment_status='Pending'
    """, (agent_id,))

    accepted_notifications = fetch_all(cursor)

    cursor.execute("""
        SELECT
            properties.*,
            banks.bankname
        FROM properties
        JOIN banks ON properties.bank_id = banks.id
        WHERE properties.status='Available'
        ORDER BY properties.id DESC
    """)
    properties = fetch_all(cursor)

    cursor.execute("""
        SELECT *
        FROM agents
        WHERE id=%s
    """, (agent_id,))
    agent = fetch_one(cursor)

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
    """, (agent_id,))
    total_offers = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
        AND status='Accepted'
    """, (agent_id,))
    accepted_offers = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
        AND status='Rejected'
    """, (agent_id,))
    rejected_offers = cursor.fetchone()['total']

    #notification
    cursor.execute("""
    SELECT *
    FROM notifications
    WHERE receiver_type='agent'
    AND receiver_id=%s
    AND is_read=0
    ORDER BY id DESC
    """, (agent_id,))

    notifications = fetch_all(cursor)
    cursor.close()

    return render_template(
        'agent/agent_dashboard.html',
        properties=properties,
        agent_id=agent_id,
        agent=agent,
        accepted_notifications=accepted_notifications,
        total_properties=len(properties),
        total_offers=total_offers,
        accepted_offers=accepted_offers,
        rejected_offers=rejected_offers,
        notifications=notifications
    )

# UPDATE AGENT PROFILE

@app.route('/agent/update_profile/<int:agent_id>', methods=['POST'])
def update_profile(agent_id):
    cursor = mysql.connection.cursor()

    fullname = request.form['fullname']
    agency = request.form['agency']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    cursor.execute("""
        SELECT profile_image
        FROM agents
        WHERE id=%s
    """, (agent_id,))
    data = fetch_one(cursor)

    if not data:
        cursor.close()
        return 'Agent not found'

    profile_image = data['profile_image']
    profile = request.files.get('profile_image')

    if profile and profile.filename.strip() != '':
        filename = f"{uuid.uuid4().hex}_{secure_filename(profile.filename)}"
        profile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        profile_image = filename

    cursor.execute("""
        UPDATE agents
        SET
            fullname=%s,
            agency=%s,
            email=%s,
            phone=%s,
            address=%s,
            profile_image=%s
        WHERE id=%s
    """, (
        fullname,
        agency,
        email,
        phone,
        address,
        profile_image,
        agent_id
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect(f'/agent/agent_dashboard/{agent_id}')

# OFFER PRICE

@app.route('/agent/offer_price/<int:property_id>/<int:agent_id>', methods=['POST'])
def offer_price(property_id, agent_id):
    cursor = mysql.connection.cursor()

    offer_price_value = int(request.form['offer_price'])

    cursor.execute("""
        SELECT minimum_price
        FROM properties
        WHERE id=%s
    """, (property_id,))
    property_data = fetch_one(cursor)

    if not property_data:
        cursor.close()
        return 'Property not found'

    minimum_price = property_data['minimum_price']

    if offer_price_value < minimum_price:
        cursor.close()
        return """
        <h1 style='color:red;text-align:center;margin-top:100px;'>
        Offer Must Be Higher Than Minimum Price
        </h1>
        """

    cursor.execute("""
        INSERT INTO property_offers
        (
            property_id,
            agent_id,
            offer_price
        )
        VALUES (%s,%s,%s)
    """, (
        property_id,
        agent_id,
        offer_price_value
    ))

    mysql.connection.commit()
#notificaion offer_price
    cursor.execute("""
    SELECT bank_id,property_name
    FROM properties
    WHERE id=%s
    """, (property_id,))

    property = cursor.fetchone()

    cursor.execute("""
    INSERT INTO notifications
    (receiver_type,receiver_id,title,message,icon)
    VALUES(%s,%s,%s,%s,%s)
    """, (
        'bank',
        property['bank_id'],
        'New Offer',
        f'Agent submitted an offer for {property["property_name"]}',
        'fa-money-bill'
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect(f'/agent/agent_dashboard/{agent_id}')


# ======================================================
# VIEW OFFERS
# ======================================================

@app.route('/bank/view_offers/<int:property_id>')
def view_offers(property_id):
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            property_offers.id,
            agents.fullname,
            property_offers.offer_price,
            property_offers.status
        FROM property_offers
        JOIN agents ON property_offers.agent_id = agents.id
        WHERE property_offers.property_id=%s
        ORDER BY property_offers.offer_price DESC
    """, (property_id,))
    offers = fetch_all(cursor)

    cursor.close()

    return render_template(
        'bank/view_offers.html',
        offers=offers,
        property_id=property_id
    )

# ACCEPT OFFER

# REJECT OFFER


@app.route('/bank/reject_offer/<int:offer_id>/<int:property_id>')
def reject_offer(offer_id, property_id):

    cursor = mysql.connection.cursor()

    # Reject the offer
    cursor.execute("""
        UPDATE property_offers
        SET status='Rejected'
        WHERE id=%s
    """, (offer_id,))

    # Make property available if no accepted offers remain
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE property_id=%s
        AND status='Accepted'
    """, (property_id,))

    accepted = cursor.fetchone()['total']

    if accepted == 0:
        cursor.execute("""
            UPDATE properties
            SET status='Available'
            WHERE id=%s
        """, (property_id,))

    # Get agent details
    cursor.execute("""
        SELECT
            agent_id,
            property_id
        FROM property_offers
        WHERE id=%s
    """, (offer_id,))

    offer = cursor.fetchone()

    agent_id = offer['agent_id']

    # Get property name
    cursor.execute("""
        SELECT property_name
        FROM properties
        WHERE id=%s
    """, (offer['property_id'],))

    property_name = cursor.fetchone()['property_name']

    # Send notification to the agent
    cursor.execute("""
        INSERT INTO notifications
        (receiver_type, receiver_id, title, message, icon)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'agent',
        agent_id,
        'Offer Rejected',
        f'Your offer for "{property_name}" has been rejected by the bank.',
        'fa-circle-xmark'
    ))

    mysql.connection.commit()
    cursor.close()

    flash("Offer rejected successfully.", "success")

    return redirect(f"/bank/view_offers/{property_id}")
#-----------------------------------------------------------------------------------------------------------------------------------

@app.route('/bank/accept_offer/<int:offer_id>/<int:property_id>')
def accept_offer(offer_id, property_id):

    cursor = mysql.connection.cursor()

    # Check if property is already sold
    cursor.execute("""
        SELECT status
        FROM properties
        WHERE id=%s
    """, (property_id,))

    property_data = cursor.fetchone()

    if property_data['status'] == 'Sold':
        flash('Property already sold!', 'error')
        cursor.close()
        return redirect(f'/bank/view_offers/{property_id}')

    # Accept selected offer
    cursor.execute("""
    UPDATE property_offers
    SET
        status='Accepted',
        payment_status='Pending',
        accepted_time=NOW()
    WHERE id=%s
    """, (offer_id,))
    # Reject all other offers
    cursor.execute("""
        UPDATE property_offers
        SET status='Rejected'
        WHERE property_id=%s
        AND id!=%s
    """, (property_id, offer_id))

    # Property is waiting for payment
    cursor.execute("""
        UPDATE properties
        SET status='Pending'
        WHERE id=%s
    """, (property_id,))

    cursor.execute("""
    UPDATE properties
    SET status='Pending'
    WHERE id=%s
    """, (property_id,))

    mysql.connection.commit()

    cursor.execute("""
    SELECT agent_id
    FROM property_offers
    WHERE id=%s
    """, (offer_id,))

    agent_id = cursor.fetchone()['agent_id']
#notification

    cursor.execute("""
    INSERT INTO notifications
    (receiver_type,receiver_id,title,message,icon)
    VALUES(%s,%s,%s,%s,%s)
    """, (
        'agent',
        agent_id,
        'Offer Accepted',
        'Your property offer has been accepted.',
        'fa-check'
    ))

    mysql.connection.commit()
    cursor.close()

    flash("Offer accepted. Waiting for agent payment.", "success")

    return redirect(f'/bank/view_offers/{property_id}')

# ======================================================
# paymet page
# ======================================================
# PAYMENT PAGE
# ======================================================

@app.route('/payment/<int:offer_id>')
def payment_page(offer_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            property_offers.*,
            properties.property_name,
            properties.location,
            properties.image,
            properties.bank_id
        FROM property_offers
        JOIN properties
            ON property_offers.property_id = properties.id
        WHERE property_offers.id = %s
    """, (offer_id,))

    offer = fetch_one(cursor)

    cursor.close()

    if not offer:
        flash("Offer not found.", "error")
        return redirect('/')

    return render_template(
        "payment.html",
        offer=offer
    )

#chaneges in bank darshboard slide bar


@app.route('/bank/profile/<int:bank_id>')
def bank_profile(bank_id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM banks WHERE id=%s",
        (bank_id,)
    )

    bank = fetch_one(cursor)

    return render_template(
        'bank/profile.html',
        bank=bank,
        bank_id=bank_id
    )


    bank = fetch_one(cursor)

    return render_template(
        'bank/profile.html',
        bank=bank,
        bank_id=bank_id
    )

@app.route('/bank/analytics/<int:bank_id>')
def bank_analytics(bank_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM banks
        WHERE id=%s
    """,(bank_id,))
    bank = fetch_one(cursor)

    cursor.execute("""
        SELECT COUNT(*) total
        FROM properties
        WHERE bank_id=%s
    """,(bank_id,))
    total_properties = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM properties
        WHERE bank_id=%s
        AND status='Available'
    """,(bank_id,))
    available_properties = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM properties
        WHERE bank_id=%s
        AND status='Sold'
    """,(bank_id,))
    sold_properties = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM property_offers
        JOIN properties
        ON property_offers.property_id=properties.id
        WHERE properties.bank_id=%s
    """,(bank_id,))
    total_offers = cursor.fetchone()['total']

    cursor.close()

    return render_template(
        "bank/analytics.html",
        bank=bank,
        bank_id=bank_id,
        total_properties=total_properties,
        available_properties=available_properties,
        sold_properties=sold_properties,
        total_offers=total_offers
    )
@app.route('/bank/properties/<int:bank_id>')
def bank_properties(bank_id):

    cursor = mysql.connection.cursor()

    # Get bank details
    cursor.execute("""
        SELECT *
        FROM banks
        WHERE id=%s
    """,(bank_id,))
    bank = fetch_one(cursor)

    # Get properties
    cursor.execute("""
        SELECT *
        FROM properties
        WHERE bank_id=%s
        ORDER BY id DESC
    """,(bank_id,))
    properties = fetch_all(cursor)

    cursor.close()

    return render_template(
        "bank/properties.html",
        bank=bank,
        properties=properties,
        bank_id=bank_id
    )
#new changes on agent drashboard

@app.route('/agent/profile/<int:agent_id>')
def agent_profile_page(agent_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
    SELECT *
    FROM agents
    WHERE id=%s
    """, (agent_id,))

    agent = fetch_one(cursor)

    cursor.close()

    return render_template(
        'agent/profile.html',
        agent=agent,
        agent_id=agent_id
    )
@app.route('/payment_success/<int:offer_id>', methods=['POST'])
def payment_success(offer_id):

    cursor = mysql.connection.cursor()

    transaction = "TXN" + str(random.randint(10000000, 99999999))

    # Update payment details
    cursor.execute("""
        UPDATE property_offers
        SET
            payment_status='Paid',
            payment_date=NOW(),
            transaction_id=%s
        WHERE id=%s
    """, (transaction, offer_id))

    # Get property and agent details
    cursor.execute("""
        SELECT property_id, agent_id
        FROM property_offers
        WHERE id=%s
    """, (offer_id,))

    data = cursor.fetchone()

    property_id = data['property_id']
    agent_id = data['agent_id']

    # Mark property as Sold
    cursor.execute("""
        UPDATE properties
        SET status='Sold'
        WHERE id=%s
    """, (property_id,))

    # Get bank id and property name
    cursor.execute("""
        SELECT bank_id, property_name
        FROM properties
        WHERE id=%s
    """, (property_id,))

    property_data = cursor.fetchone()

    bank_id = property_data['bank_id']
    property_name = property_data['property_name']

    # Notification for Bank
    cursor.execute("""
        INSERT INTO notifications
        (receiver_type, receiver_id, title, message, icon)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'bank',
        bank_id,
        'Payment Received',
        f'Payment received for "{property_name}".',
        'fa-credit-card'
    ))

    # Notification for Admin
    cursor.execute("""
        INSERT INTO notifications
        (receiver_type, receiver_id, title, message, icon)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        'admin',
        1,
        'Property Sold',
        f'"{property_name}" has been sold successfully.',
        'fa-building'
    ))

    mysql.connection.commit()
    cursor.close()

    flash("Payment Successful", "success")

    return redirect(f"/agent/my_properties/{agent_id}")

@app.route('/agent/my_properties/<int:agent_id>')
def my_properties(agent_id):
    reset_expired_pending_properties()
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM agents
        WHERE id=%s
    """,(agent_id,))
    agent = fetch_one(cursor)

    cursor.execute("""
        SELECT
            properties.*,
            banks.bankname,
            property_offers.id AS offer_id,
            property_offers.offer_price,
            property_offers.payment_status,
            property_offers.payment_date,
            property_offers.transaction_id
        FROM property_offers
        JOIN properties
            ON property_offers.property_id=properties.id
        JOIN banks
            ON properties.bank_id=banks.id
        WHERE property_offers.agent_id=%s
        AND property_offers.status='Accepted'
    """,(agent_id,))

    properties = fetch_all(cursor)

    cursor.close()

    return render_template(
        "agent/my_properties.html",
        properties=properties,
        agent=agent,
        agent_id=agent_id
    )

#property agent
@app.route('/agent/properties/<int:agent_id>')
def agent_properties_page(agent_id):

    cursor = mysql.connection.cursor()

    # Agent Details
    cursor.execute("""
        SELECT *
        FROM agents
        WHERE id=%s
    """, (agent_id,))
    agent = fetch_one(cursor)

    # Available Properties with map_link
    cursor.execute("""
        SELECT
            properties.*,
            banks.bankname
        FROM properties
        JOIN banks
            ON properties.bank_id = banks.id
        WHERE properties.status='Available'
        ORDER BY properties.id DESC
    """)
    properties = fetch_all(cursor)

    # Total Offers
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
    """, (agent_id,))
    total_offers = cursor.fetchone()['total']

    # Accepted Offers
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
        AND status='Accepted'
    """, (agent_id,))
    accepted_offers = cursor.fetchone()['total']

    # Rejected Offers
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM property_offers
        WHERE agent_id=%s
        AND status='Rejected'
    """, (agent_id,))
    rejected_offers = cursor.fetchone()['total']

    cursor.close()

    return render_template(
        "agent/properties.html",
        agent=agent,
        properties=properties,
        agent_id=agent_id,
        total_properties=len(properties),
        total_offers=total_offers,
        accepted_offers=accepted_offers,
        rejected_offers=rejected_offers
    )
#pending bank
@app.route('/bank/pending_offer/<int:offer_id>/<int:property_id>')
def pending_offer(offer_id, property_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE property_offers
        SET
            status='Accepted',
            payment_status='Pending'
        WHERE id=%s
    """, (offer_id,))

    cursor.execute("""
        UPDATE property_offers
        SET status='Rejected'
        WHERE property_id=%s
        AND id!=%s
    """, (property_id, offer_id))

    cursor.execute("""
        UPDATE properties
        SET status='Pending'
        WHERE id=%s
    """, (property_id,))

    mysql.connection.commit()
    cursor.close()

    flash("Property is waiting for agent payment.", "success")

    return redirect(f"/bank/view_offers/{property_id}")

def reset_expired_pending_properties():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE properties p
        JOIN property_offers o
            ON p.id=o.property_id
        SET
            p.status='Available',
            o.status='Expired'
        WHERE
            p.status='Pending'
            AND o.payment_status='Pending'
            AND TIMESTAMPDIFF(HOUR,o.accepted_time,NOW())>=1
    """)
    mysql.connection.commit()
    cursor.close()


@app.route("/notification/read/<int:id>")
def read_notification(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read=1
        WHERE id=%s
    """, (id,))

    mysql.connection.commit()
    cursor.close()

    return "", 204

@app.route("/notification/clear/<receiver>/<int:id>")
def clear_notifications(receiver, id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read=1
        WHERE receiver_type=%s
        AND receiver_id=%s
    """, (receiver, id))

    mysql.connection.commit()
    cursor.close()

    return redirect(request.referrer)
@app.context_processor
def load_admin_notifications():

    # Only load on admin pages
    if request.path.startswith('/admin/'):

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM notifications
            WHERE receiver_type='admin'
            ORDER BY id DESC
        """)

        notifications = fetch_all(cursor)

        cursor.close()

        return {
            'notifications': notifications
        }

    return {}


if __name__ == '__main__':
    app.run(debug=True)
