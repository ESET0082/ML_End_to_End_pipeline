import os
import pandas as pd
from sqlalchemy import create_engine, text

class FeatureEngineering:

    def __init__(self):
        # === Database Configuration ===
        self.db_user = "postgres"
        self.db_pass = "postgres"
        self.db_host = "localhost"
        self.db_port = "5432"
        self.db_name = "meter_db"

        # === Output Path ===
        self.output_dir = r"D:\Advanced ML Project Final\final_project_repo\data\raw"
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, "final_meter_features.csv")

        # === SQLAlchemy Engine ===
        self.engine = create_engine(
            f"postgresql+psycopg2://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # -----------------------------
    # Step 1: Load Data from Postgres
    # -----------------------------
    def load_data(self):
        print("📥 Loading data from PostgreSQL...")

        query = """
            SELECT 
                md.*, 
                c.name, c.mobile_number, c.address, c.city, c.pincode,
                c.connection_type, c.tariff_plan, c.connection_date
            FROM meter_data md
            LEFT JOIN customers c 
            ON md.meter_id = c.meter_id;
        """

        # Use connection with proper execution
        from sqlalchemy import text as sql_text
        with self.engine.connect() as connection:
            result = connection.execute(sql_text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        # Convert reading_date → datetime
        if "reading_date" not in df.columns:
            raise ValueError("❌ 'reading_date' column missing!")

        df["date"] = pd.to_datetime(df["reading_date"])

        print("✅ Loaded:", df.shape)
        return df

    # -----------------------------
    # Step 2: Feature Engineering
    # -----------------------------
    def create_features(self, df):
        print("⚙️ Creating features...")

        # Convert Decimal columns to float for arithmetic operations
        decimal_cols = df.select_dtypes(include=['object']).columns
        for col in decimal_cols:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        # Basic Date Features
        df["hour"] = df["date"].dt.hour
        df["day_of_week"] = df["date"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Voltage Abnormality
        df["voltage_status"] = df["voltage"].apply(
            lambda v: "low" if v < 180 else ("high" if v > 250 else "normal")
        )
        df["voltage_flag"] = df["voltage_status"].map({"low": 0, "normal": 1, "high": 2})

        # Power Factor Issue
        df["pf_issue"] = (df["power_factor"] < 0.85).astype(int)

        # High Temperature
        df["high_temp"] = (df["temperature"] > 40).astype(int)

        # Load Consumption Intensity (convert to float first)
        df["load_intensity"] = pd.to_numeric(df["units"], errors='coerce') / (pd.to_numeric(df["load_kw"], errors='coerce') + 1e-5)

        print("✅ Features created.")
        return df

    # -----------------------------
    # Step 3: Remove Unnecessary Columns
    # -----------------------------
    def remove_unnecessary_columns(self, df):
        print("🧹 Removing unnecessary columns...")

        drop_cols = [
            "name", "mobile_number", "address", "city", "pincode",
            "connection_type", "tariff_plan", "connection_date",
            "phase", "status", "reading_date"
        ]

        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

        print("✅ Columns removed.")
        return df

    # -----------------------------
    # Step 4: Save Final CSV
    # -----------------------------
    def save_data(self, df):
        df.to_csv(self.output_file, index=False)
        print(f"💾 Saved to: {self.output_file}")

    # -----------------------------
    # Step 5: Pipeline Run
    # -----------------------------
    def run(self):
        print("🚀 Running Feature Engineering Pipeline...")
        df = self.load_data()
        df = self.create_features(df)
        df = self.remove_unnecessary_columns(df)
        self.save_data(df)
        print("🎉 Pipeline Completed Successfully!")


# Run script
if __name__ == "__main__":
    fe = FeatureEngineering()
    fe.run()


# Module-level helper functions for easier imports in tests and other modules
def load_data():
    """Load data from the configured source and return a DataFrame.

    This wraps `FeatureEngineering.load_data` so callers can do:
    `from data.create_datasets import load_data` in tests or scripts.
    """
    fe = FeatureEngineering()
    return fe.load_data()


def create_features(df):
    """Create features on the provided DataFrame.

    Wraps `FeatureEngineering.create_features` to allow importing directly
    from the module in tests.
    """
    fe = FeatureEngineering()
    return fe.create_features(df)
