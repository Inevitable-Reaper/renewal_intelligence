import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataIngestionPipeline:
    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        self.raw_dir = Path(raw_data_dir)
        self.processed_dir = Path(processed_data_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.accounts = None
        self.usage = None
        self.tickets = None
        self.nps = None
        self.csm_notes = ""
        self.changelog = ""

    def load_raw_data(self):
        """Loads and normalizes raw files from the data directory safely."""
        logging.info("Loading raw data files...")
        
        # 1. Helper function to instantly clean columns right as the file is read
        def read_and_clean(filename):
            path = self.raw_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing required data file: {path}")
            
            df = pd.read_csv(path)
            # Force headers to strict lowercase snake_case
            df.columns = (
                df.columns.str.lower()
                .str.replace(r"[^a-z0-9_\s]", "", regex=True)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True)
            )
            return df

        # 2. Safely read and clean each dataframe individually (No loops, no NoneType errors)
        self.accounts = read_and_clean("accounts.csv")
        self.usage = read_and_clean("usage_metrics.csv")
        self.tickets = read_and_clean("support_tickets.csv")
        self.nps = read_and_clean("nps_responses.csv")
        
        # 3. Read the text assets
        with open(self.raw_dir / "csm_notes.txt", "r", encoding="utf-8") as f:
            self.csm_notes = f.read()
            
        with open(self.raw_dir / "changelog.md", "r", encoding="utf-8") as f:
            self.changelog = f.read()

        # 4. Rename specific complex headers to match engine.py exactly
        self.accounts = self.accounts.rename(columns={"arr_": "arr"})
        self.usage = self.usage.rename(columns={"month": "month_index"})
        self.nps = self.nps.rename(columns={
            "nps_score_010": "nps_score",
            "surveydate": "survey_date"
        })
        
        with open(self.raw_dir / "csm_notes.txt", "r", encoding="utf-8") as f:
            self.csm_notes = f.read()
            
        with open(self.raw_dir / "changelog.md", "r", encoding="utf-8") as f:
            self.changelog = f.read()

        # MASTER CLEANER: Force all column headers to snake_case, removing spaces and special symbols
        for df in [self.accounts, self.usage, self.tickets, self.nps]:
            df.columns = (
                df.columns.str.lower()
                .str.replace(r"[^a-z0-9_\s]", "", regex=True) # strip brackets and symbols like ($)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True) # replace internal spaces with underscores
            )

        # Standardize explicit messy names found in your specific files
        self.accounts = self.accounts.rename(columns={"arr_": "arr"})
        self.usage = self.usage.rename(columns={"month": "month_index"})
        self.nps = self.nps.rename(columns={"nps_score_010": "nps_score"})

    def resolve_entities(self) -> pd.DataFrame:
        """Resolves messy account names using fuzzy matching."""
        logging.info("Resolving entity naming inconsistencies...")
        master_lookup = dict(zip(self.accounts['account_name'], self.accounts['account_id']))
        true_names = list(master_lookup.keys())
        
        def get_best_match_id(messy_name):
            if pd.isna(messy_name):
                return None
            match = process.extractOne(str(messy_name), true_names, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= 75:  
                return master_lookup[match[0]]
            return None

        # Clean datasets that rely on names instead of IDs
        for df in [self.tickets, self.nps]:
            if 'account_name' in df.columns and 'account_id' not in df.columns:
                df['account_id'] = df['account_name'].apply(get_best_match_id)
                
        return self.accounts

    def run_pipeline(self):
        """Executes ingestion, cleans data, and saves checkpoints to processed/ folder."""
        self.load_raw_data()
        self.resolve_entities()
        
        self.accounts.to_csv(self.processed_dir / "clean_accounts.csv", index=False)
        self.usage.to_csv(self.processed_dir / "clean_usage.csv", index=False)
        self.tickets.to_csv(self.processed_dir / "clean_tickets.csv", index=False)
        self.nps.to_csv(self.processed_dir / "clean_nps.csv", index=False)
        logging.info("Ingestion complete. Cleaned datasets cached.")