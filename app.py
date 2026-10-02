from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import joblib
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "smart-grid-local-secret-key"

MODEL_PATH = "models/model.pkl"
model = joblib.load(MODEL_PATH)


def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password=os.getenv("MYSQL_PASSWORD"),
        database="smart_grid_db"
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            query = """
                INSERT INTO users (name, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(query, (name, email, password))
            connection.commit()

        except mysql.connector.Error as error:

            connection.rollback()
            cursor.close()
            connection.close()

            return f"Registration failed: {error}"

        cursor.close()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT * FROM users
            WHERE email = %s AND password = %s
        """

        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("prediction"))

        return "Invalid email or password"

    return render_template("login.html")


@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # ------------------------------------------------
    # Default values
    # ------------------------------------------------

    result = None
    current_load = None

    load_difference = None
    balance_status = None
    renewable_power = None

    voltage = ""
    current = ""
    reactive_power = ""
    power_factor = ""
    solar_power = ""
    wind_power = ""
    wind_radius = ""
    latitude = ""
    longitude = ""

    # ------------------------------------------------
    # Prediction
    # ------------------------------------------------

    if request.method == "POST":

        # Get values entered by user
        voltage = request.form["voltage"]
        current = request.form["current"]
        reactive_power = request.form["reactive_power"]
        power_factor = request.form["power_factor"]

        solar_power = request.form["solar_power"]
        wind_power = request.form["wind_power"]

        wind_radius = request.form["wind_radius"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]

        # Convert values to numbers
        voltage_value = float(voltage)
        current_value = float(current)
        reactive_power_value = float(reactive_power)
        power_factor_value = float(power_factor)

        solar_watt = float(solar_power or 0)
        wind_watt = float(wind_power or 0)

        # Convert Watt to kW
        solar_power_kw = solar_watt / 1000
        wind_power_kw = wind_watt / 1000

        # Temporary environmental values
        temperature = 30
        humidity = 60

        # ------------------------------------------------
        # Prepare ML input
        # ------------------------------------------------

        input_data = pd.DataFrame([{

            "Voltage (V)": voltage_value,

            "Current (A)": current_value,

            "Reactive Power (kVAR)": reactive_power_value,

            "Power Factor": power_factor_value,

            "Solar Power (kW)": solar_power_kw,

            "Wind Power (kW)": wind_power_kw,

            "Temperature (°C)": temperature,

            "Humidity (%)": humidity

        }])

        # ------------------------------------------------
        # Calculate current load
        # ------------------------------------------------

        current_load = (
            voltage_value *
            current_value *
            power_factor_value
        ) / 1000

        # ------------------------------------------------
        # ML prediction
        # ------------------------------------------------

        predicted_load = model.predict(input_data)[0]

        result = round(float(predicted_load), 2)

        current_load = round(float(current_load), 2)

        # ------------------------------------------------
        # Load balancing analysis
        # ------------------------------------------------

        load_difference = round(
            result - current_load,
            2
        )

        # Determine load balance status
        if load_difference > 0.5:

            balance_status = (
                "Additional power generation is recommended."
            )

        elif load_difference < -0.5:

            balance_status = (
                "Available renewable energy can help "
                "balance the load."
            )

        else:

            balance_status = (
                "The system is approximately balanced."
            )

        # ------------------------------------------------
        # Renewable energy
        # ------------------------------------------------

        renewable_power = round(
            solar_power_kw + wind_power_kw,
            2
        )

    # ------------------------------------------------
    # Send everything to prediction.html
    # ------------------------------------------------

    return render_template(

        "prediction.html",

        result=result,

        current_load=current_load,

        load_difference=load_difference,

        balance_status=balance_status,

        renewable_power=renewable_power,

        # Entered values
        voltage=voltage,

        current=current,

        reactive_power=reactive_power,

        power_factor=power_factor,

        solar_power=solar_power,

        wind_power=wind_power,

        wind_radius=wind_radius,

        latitude=latitude,

        longitude=longitude
    )

@app.route("/energy-insights", methods=["GET", "POST"])
def energy_insights():

    if "user_id" not in session:
        return redirect(url_for("login"))

    energy_result = False
    average_energy = None
    average_temperature = None
    energy_values = []
    temperature_values = []
    suggestions = []

    if request.method == "POST":

        file = request.files.get("energy_file")

        if file is None or file.filename == "":
            return "Please upload a CSV file."

        try:

            df = pd.read_csv(file)

            energy_column = None
            temperature_column = None

            for column in df.columns:

                column_lower = column.lower()

                if "energy" in column_lower:
                    energy_column = column

                if "temperature" in column_lower:
                    temperature_column = column

            if energy_column is None:
                return "CSV must contain an Energy column."

            if temperature_column is None:
                return "CSV must contain a Temperature column."

            df[energy_column] = pd.to_numeric(
                df[energy_column],
                errors="coerce"
            )

            df[temperature_column] = pd.to_numeric(
                df[temperature_column],
                errors="coerce"
            )

            df = df.dropna(
                subset=[
                    energy_column,
                    temperature_column
                ]
            )

            energy_values = df[energy_column].tolist()

            temperature_values = df[temperature_column].tolist()

            average_energy = round(
                float(df[energy_column].mean()),
                2
            )

            average_temperature = round(
                float(df[temperature_column].mean()),
                2
            )

            energy_result = True

            if average_energy > 500:
                suggestions.append(
                    "Energy consumption is relatively high. "
                    "Consider reducing unnecessary electrical loads."
                )
            else:
                suggestions.append(
                    "Energy consumption is within the analyzed range."
                )

            if average_temperature > 30:
                suggestions.append(
                    "Higher temperature may increase energy demand. "
                    "Consider improving cooling efficiency."
                )
            else:
                suggestions.append(
                    "Temperature levels are within the analyzed range."
                )

        except Exception as error:

            return f"Error processing CSV file: {error}"

    return render_template(
        "energy_insights.html",
        energy_result=energy_result,
        average_energy=average_energy,
        average_temperature=average_temperature,
        energy_values=energy_values,
        temperature_values=temperature_values,
        suggestions=suggestions
    )
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT * FROM admin
            WHERE email = %s AND password = %s
        """

        cursor.execute(query, (email, password))

        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]

            return "Admin login successful"

        return "Invalid admin email or password"

    return render_template("admin_login.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":

    app.run(debug=True)