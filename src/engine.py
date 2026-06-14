import pandas as pd
import numpy as np
from pathlib import Path

class RiskScoringEngine:
    def __init__(self, processed_data_dir: str):
        self.processed_dir = Path(processed_data_dir)
        self.accounts = pd.read_csv(self.processed_dir / "clean_accounts.csv")
        self.usage = pd.read_csv(self.processed_dir / "clean_usage.csv")
        self.tickets = pd.read_csv(self.processed_dir / "clean_tickets.csv")
        self.nps = pd.read_csv(self.processed_dir / "clean_nps.csv")

    def analyze_usage_trends(self) -> pd.DataFrame:
        """Calculates Month-over-Month (MoM) usage trends on standardized headers."""
        self.usage = self.usage.sort_values(by=['account_id', 'month_index'])
        
        trends = []
        for acct_id, group in self.usage.groupby('account_id'):
            if len(group) >= 2:
                initial_usage = group.iloc[:2]['api_calls'].mean()
                recent_usage = group.iloc[-2:]['api_calls'].mean()
                mom_change = ((recent_usage - initial_usage) / (initial_usage + 1e-5))
            else:
                mom_change = 0.0
            
            trends.append({'account_id': acct_id, 'usage_mom_change': mom_change})
            
        return pd.DataFrame(trends)

    def analyze_support_health(self) -> pd.DataFrame:
        """Aggregates ticket count burdens using your exact file's 'priority' metrics."""
        ticket_summary = self.tickets.groupby('account_id').agg(
            total_tickets=('ticket_id', 'count'),
            high_sev_tickets=('priority', lambda x: (x.astype(str).str.lower().isin(['high', 'p1', 'p0', 'critical'])).sum())
        ).reset_index()
        return ticket_summary

    def analyze_nps(self) -> pd.DataFrame:
        if 'score' in self.nps.columns:
            return self.nps.groupby('account_id')['score'].mean().reset_index().rename(columns={'score': 'nps_score'})
        elif 'nps_score' in self.nps.columns:
            return self.nps.groupby('account_id')['nps_score'].mean().reset_index()
    
    # Fallback to an empty DataFrame with expected columns if the asset is completely broken
        return pd.DataFrame(columns=['account_id', 'nps_score'])
    
    def compute_risk_matrix(self) -> pd.DataFrame:
        """Compiles features and builds a hybrid algorithmic scoring matrix."""
        usage_df = self.analyze_usage_trends()
        ticket_df = self.analyze_support_health()
        nps_df = self.analyze_nps()

        master_df = self.accounts.merge(usage_df, on='account_id', how='left')
        master_df = master_df.merge(ticket_df, on='account_id', how='left')
        master_df = master_df.merge(nps_df, on='account_id', how='left')

        master_df['usage_mom_change'] = master_df['usage_mom_change'].fillna(0.0)
        master_df['total_tickets'] = master_df['total_tickets'].fillna(0)
        master_df['high_sev_tickets'] = master_df['high_sev_tickets'].fillna(0)
        master_df['nps_score'] = master_df['nps_score'].fillna(8) 

        master_df['algo_risk_score'] = 0
        
        # Scoring Rules
        master_df.loc[master_df['usage_mom_change'] <= -0.25, 'algo_risk_score'] += 3
        master_df.loc[(master_df['usage_mom_change'] > -0.25) & (master_df['usage_mom_change'] <= -0.10), 'algo_risk_score'] += 1
        master_df.loc[master_df['nps_score'] <= 6, 'algo_risk_score'] += 3
        master_df.loc[master_df['high_sev_tickets'] >= 3, 'algo_risk_score'] += 2

        def assign_tier(score):
            if score >= 5: return "High"
            if score >= 2: return "Medium"
            return "Low"

        master_df['quantitative_risk_tier'] = master_df['algo_risk_score'].apply(assign_tier)
        return master_df