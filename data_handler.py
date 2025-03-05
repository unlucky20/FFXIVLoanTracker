import pandas as pd
import os
from datetime import datetime
from lodestone_scraper import LodestoneScraper
import shutil
import zipfile
from git_sync import GitSync

class DataManager:
    def __init__(self, fc_id="9228157111459014466"):
        # Use a persistent directory path for Replit
        self.data_dir = os.path.join(os.environ.get('REPL_HOME', ''), 'data')
        self.donations_path = os.path.join(self.data_dir, "donations.csv")
        self.members_path = os.path.join(self.data_dir, "members.csv")
        self.expenses_path = os.path.join(self.data_dir, "expenses.csv")
        self.bids_path = os.path.join(self.data_dir, "bids.csv")
        self.expense_categories = ['Housing', 'Giveaways', 'Events', 'Crafting', 'Other']

        # Ensure data directory exists with proper permissions
        os.makedirs(self.data_dir, mode=0o755, exist_ok=True)

        # Create backup directory
        backup_dir = os.path.join(self.data_dir, "backups")
        os.makedirs(backup_dir, mode=0o755, exist_ok=True)

        # Initialize Git sync
        self.git_sync = GitSync(self.data_dir)
        self.git_sync.init_repo()
        self.git_sync.pull_changes()  # Pull latest changes on startup

        self.ensure_csv_exists()
        self.lodestone = LodestoneScraper(fc_id)

    def ensure_csv_exists(self):
        """Initialize CSV files if they don't exist"""
        try:
            # Initialize CSV files with default structure
            default_files = {
                self.members_path: ['name', 'join_date'],
                self.donations_path: ['member_name', 'amount', 'date', 'notes', 'timestamp'],
                self.expenses_path: ['date', 'amount', 'description', 'category', 'approved_by'],
                self.bids_path: ['member_name', 'bid_number', 'date']
            }

            for file_path, columns in default_files.items():
                if not os.path.exists(file_path):
                    df = pd.DataFrame(columns=columns)
                    df.to_csv(file_path, index=False)
                else:
                    # Verify file is readable and writable
                    with open(file_path, 'r') as f:
                        pd.read_csv(f)  # Test read
                    with open(file_path, 'a') as f:
                        f.write("")  # Test write
        except Exception as e:
            print(f"Error ensuring CSV files exist: {str(e)}")
            raise

    def backup_data(self):
        """Create a backup of all data files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_folder = os.path.join(self.data_dir, f"backups/backup_{timestamp}")
            os.makedirs(os.path.dirname(backup_folder), exist_ok=True)

            # Copy all CSV files to backup folder
            for file_name in ["donations.csv", "members.csv", "expenses.csv", "bids.csv"]:
                src = os.path.join(self.data_dir, file_name)
                dst = os.path.join(backup_folder, file_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)

            print(f"✅ Backup created successfully at {backup_folder}")
            return True
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")
            return False

    def restore_latest_backup(self):
        """Restore the most recent backup"""
        try:
            # Get list of backup folders
            backup_folders = [d for d in os.listdir(os.path.join(self.data_dir,"backups")) 
                            if os.path.isdir(os.path.join(os.path.join(self.data_dir,"backups"), d))]

            if not backup_folders:
                print("No backups found")
                return False

            # Get most recent backup folder
            latest_backup = max(backup_folders)
            backup_folder = os.path.join(os.path.join(self.data_dir,"backups"), latest_backup)

            # Restore all CSV files
            for file_name in ["donations.csv", "members.csv", "expenses.csv", "bids.csv"]:
                src = os.path.join(backup_folder, file_name)
                dst = os.path.join(self.data_dir, file_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)

            print(f"✅ Data restored from backup {latest_backup}")
            return True
        except Exception as e:
            print(f"❌ Error restoring backup: {str(e)}")
            return False

    def migrate_timestamps(self):
        """Ensure all donations have unique timestamps"""
        try:
            df = pd.read_csv(self.donations_path)
            if 'timestamp' not in df.columns or df['timestamp'].isna().any():
                df['timestamp'] = df.apply(
                    lambda x: f"{x['date']}_{x.name:03d}",
                    axis=1
                )
                df.to_csv(self.donations_path, index=False)
            return df
        except Exception as e:
            print(f"Error migrating timestamps: {str(e)}")
            return pd.DataFrame(columns=['member_name', 'amount', 'date', 'notes', 'timestamp'])

    def get_donations(self):
        """Get all donations with timestamp handling"""
        try:
            df = self.migrate_timestamps()
            return df.sort_values('date', ascending=False)
        except Exception as e:
            print(f"Error getting donations: {str(e)}")
            return pd.DataFrame(columns=['member_name', 'amount', 'date', 'notes', 'timestamp'])

    def sync_to_git(self):
        """Sync changes to Git repository"""
        try:
            if self.git_sync.commit_and_push():
                print("✅ Data synced to Git successfully")
                return True
            else:
                print("❌ Failed to sync data to Git")
                return False
        except Exception as e:
            print(f"❌ Error syncing to Git: {str(e)}")
            return False

    def add_donation(self, member_name, amount, notes=""):
        """Add a new donation record"""
        try:
            df = pd.read_csv(self.donations_path)
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Create unique timestamp based on date and current number of donations
            timestamp = f"{current_date}_{len(df):03d}"

            new_donation = {
                'member_name': member_name,
                'amount': amount,
                'date': current_date,
                'notes': notes,
                'timestamp': timestamp
            }

            df = pd.concat([df, pd.DataFrame([new_donation])], ignore_index=True)
            df.to_csv(self.donations_path, index=False)

            # Sync to Git after successful addition
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error adding donation: {str(e)}")
            return False

    def delete_donation(self, timestamp):
        """Delete a donation record"""
        try:
            df = self.migrate_timestamps()
            df = df[df['timestamp'] != timestamp]
            df.to_csv(self.donations_path, index=False)

            # Sync to Git after successful deletion
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error deleting donation: {str(e)}")
            return False

    def update_donation_notes(self, timestamp, new_notes):
        """Update donation notes"""
        try:
            df = self.migrate_timestamps()
            df.loc[df['timestamp'] == timestamp, 'notes'] = new_notes
            df.to_csv(self.donations_path, index=False)

            # Sync to Git after successful update
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error updating donation notes: {str(e)}")
            return False

    def get_total_fc_gil(self):
        """Calculate total FC gil from donations"""
        df = self.get_donations()
        return df['amount'].sum() if not df.empty else 0

    def get_total_expenses(self):
        """Calculate total expenses from all recorded expenses"""
        try:
            df = pd.read_csv(self.expenses_path)
            return df['amount'].sum() if not df.empty else 0
        except Exception as e:
            print(f"Error calculating total expenses: {e}")
            return 0

    def get_dashboard_stats(self):
        """Get overall financial statistics for the dashboard"""
        try:
            donations = self.get_total_fc_gil()
            expenses = self.get_total_expenses()
            fc_balance = donations - expenses

            return {
                'total_donations': donations,
                'total_expenses': expenses,
                'fc_balance': fc_balance
            }
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {
                'total_donations': 0,
                'total_expenses': 0,
                'fc_balance': 0
            }

    def get_all_members(self):
        """Get all FC members"""
        if not os.path.exists(self.members_path):
            self.ensure_csv_exists()
        return pd.read_csv(self.members_path)

    def sync_members_from_lodestone(self):
        """Sync members from Lodestone to local CSV"""
        try:
            print("🔄 Starting member sync...")
            lodestone_members = self.lodestone.get_all_members()

            if lodestone_members:
                unique_members = list(dict.fromkeys(lodestone_members))
                df = pd.DataFrame({
                    'name': unique_members,
                    'join_date': datetime.now().strftime('%Y-%m-%d')
                })
                df.to_csv(self.members_path, index=False)
                return len(unique_members)
            return 0
        except Exception as e:
            print(f"Error syncing members: {str(e)}")
            return 0

    # Housing Bids Methods
    def add_bid(self, member_name, bid_number):
        """Add a new housing bid"""
        df = pd.read_csv(self.bids_path)
        new_bid = {
            'member_name': member_name,
            'bid_number': bid_number,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        df = pd.concat([df, pd.DataFrame([new_bid])], ignore_index=True)
        df.to_csv(self.bids_path, index=False)

    def delete_bid(self, member_name, bid_number, date):
        """Delete a bid"""
        df = pd.read_csv(self.bids_path)
        mask = (df['member_name'] == member_name) & (df['bid_number'] == bid_number) & (df['date'] == date)
        df = df[~mask]
        df.to_csv(self.bids_path, index=False)

    def update_bid_number(self, member_name, old_bid_number, date, new_bid_number):
        """Update a bid number"""
        df = pd.read_csv(self.bids_path)
        mask = (df['member_name'] == member_name) & (df['bid_number'] == old_bid_number) & (df['date'] == date)
        df.loc[mask, 'bid_number'] = new_bid_number
        df.to_csv(self.bids_path, index=False)

    def get_member_bids(self, member_name):
        """Get all bids for a specific member"""
        df = pd.read_csv(self.bids_path)
        return df[df['member_name'] == member_name]

    # Expense Methods
    def add_expense(self, amount, description, category, approved_by):
        """Add a new expense"""
        try:
            df = pd.read_csv(self.expenses_path)
            new_expense = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'amount': amount,
                'description': description,
                'category': category,
                'approved_by': approved_by
            }
            df = pd.concat([df, pd.DataFrame([new_expense])], ignore_index=True)
            df.to_csv(self.expenses_path, index=False)
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error adding expense: {str(e)}")
            return False

    def get_expenses_list(self):
        """Get all expenses"""
        return pd.read_csv(self.expenses_path)

    def get_expenses_by_category(self):
        """Get expenses grouped by category"""
        df = pd.read_csv(self.expenses_path)
        if df.empty:
            return {category: 0 for category in self.expense_categories}
        category_totals = df.groupby('category')['amount'].sum().to_dict()
        for category in self.expense_categories:
            if category not in category_totals:
                category_totals[category] = 0
        return category_totals

    def delete_expense(self, date, amount, description):
        """Delete an expense"""
        try:
            df = pd.read_csv(self.expenses_path)
            mask = (df['date'] == date) & (df['amount'] == amount) & (df['description'] == description)
            df = df[~mask]
            df.to_csv(self.expenses_path, index=False)
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error deleting expense: {str(e)}")
            return False

    def update_expense_notes(self, date, amount, description, new_description):
        """Update expense description"""
        try:
            df = pd.read_csv(self.expenses_path)
            mask = (df['date'] == date) & (df['amount'] == amount) & (df['description'] == description)
            df.loc[mask, 'description'] = new_description
            df.to_csv(self.expenses_path, index=False)
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error updating expense notes: {str(e)}")
            return False

    def get_member_donations(self, member_name):
        """Get all donations for a specific member"""
        df = pd.read_csv(self.donations_path)
        return df[df['member_name'] == member_name]

    def get_member_donation_summary(self, member_name):
        """Get summary of donations for a specific member"""
        try:
            df = self.get_donations()
            member_donations = df[df['member_name'] == member_name]

            if member_donations.empty:
                return {
                    'total_amount': 0,
                    'donation_count': 0,
                    'first_donation': None,
                    'last_donation': None,
                    'donations': []
                }

            # Sort donations by date
            member_donations = member_donations.sort_values('date', ascending=False)

            return {
                'total_amount': member_donations['amount'].sum(),
                'donation_count': len(member_donations),
                'first_donation': member_donations['date'].iloc[-1],
                'last_donation': member_donations['date'].iloc[0],
                'donations': member_donations.to_dict('records')
            }
        except Exception as e:
            print(f"Error getting member donation summary: {str(e)}")
            return None
    
    def update_member_donations_notes(self, member_name, new_notes):
        """Update notes for all donations from a member"""
        try:
            df = self.migrate_timestamps()
            df.loc[df['member_name'] == member_name, 'notes'] = new_notes
            df.to_csv(self.donations_path, index=False)
            return True
        except Exception as e:
            print(f"Error updating member donation notes: {str(e)}")
            return False

    def delete_member(self, member_name):
        """Delete a member and their associated data"""
        try:
            # Remove from members list
            members_df = pd.read_csv(self.members_path)
            members_df = members_df[members_df['name'] != member_name]
            members_df.to_csv(self.members_path, index=False)

            # Remove their bids
            bids_df = pd.read_csv(self.bids_path)
            bids_df = bids_df[bids_df['member_name'] != member_name]
            bids_df.to_csv(self.bids_path, index=False)

            #Remove their donations
            donations_df = pd.read_csv(self.donations_path)
            donations_df = donations_df[donations_df['member_name'] != member_name]
            donations_df.to_csv(self.donations_path, index=False)

            # Sync changes to Git
            self.sync_to_git()
            return True
        except Exception as e:
            print(f"Error deleting member: {str(e)}")
            return False

    def export_data_to_zip(self):
        """Export all data files to a zip file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_path = os.path.join(self.data_dir, f"fc_data_export_{timestamp}.zip")

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_name in ["donations.csv", "members.csv", "expenses.csv", "bids.csv"]:
                    file_path = os.path.join(self.data_dir, file_name)
                    if os.path.exists(file_path):
                        zipf.write(file_path, file_name)

            return zip_path
        except Exception as e:
            print(f"Error exporting data: {str(e)}")
            return None

    def import_data_from_zip(self, zip_file):
        """Import data from a zip file"""
        try:
            # Create a backup before import
            self.backup_data()

            with zipfile.ZipFile(zip_file, 'r') as zipf:
                # Verify zip contains required files
                file_list = zipf.namelist()
                required_files = ["donations.csv", "members.csv", "expenses.csv", "bids.csv"]

                if not all(file in file_list for file in required_files):
                    raise ValueError("Zip file missing required data files")

                # Extract files to data directory
                for file_name in required_files:
                    zipf.extract(file_name, self.data_dir)

            return True
        except Exception as e:
            print(f"Error importing data: {str(e)}")
            # Restore from backup if import fails
            self.restore_latest_backup()
            return False