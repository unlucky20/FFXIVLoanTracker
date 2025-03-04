import streamlit as st
import pandas as pd
import os
from data_handler import DataManager
from styles import apply_custom_styles
from datetime import datetime

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Lotus Free Company",
    page_icon="💰",
    layout="wide"
)

# Initialize session state for FC ID and data migration
if 'fc_id' not in st.session_state:
    st.session_state.fc_id = "9228157111459014466"  # Default FC ID

try:
    # Initialize data manager
    data_manager = DataManager(fc_id=st.session_state.fc_id)
    apply_custom_styles()

    # Add data migration tools in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Migration Tools")
    live_repl_id = st.sidebar.text_input(
        "Live Repl ID", 
        value="lotusfc",  # Pre-fill with the live app ID
        help="Enter the ID of your live deployment"
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Import Live Data"):
            if live_repl_id:
                if data_manager.import_data_from_live(live_repl_id):
                    st.success("Successfully imported data from live instance!")
                    st.rerun()
                else:
                    st.error("Failed to import live data")
            else:
                st.error("Please enter the Live Repl ID")

    with col2:
        if st.button("Export to Live"):
            if live_repl_id:
                if data_manager.export_data_to_live(live_repl_id):
                    st.success("Successfully exported data to live instance!")
                else:
                    st.error("Failed to export data")
            else:
                st.error("Please enter the Live Repl ID")

    # Main header
    st.markdown("<h1 class='main-header'>Lotus Free Company</h1>", unsafe_allow_html=True)

    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Donations", "Housing Bids", "Expenses", "Members List"]
    )

    # Dashboard
    if page == "Dashboard":
        stats = data_manager.get_dashboard_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("FC Gil Balance", f"{stats['fc_balance']:,.0f} gil")
            st.metric("Total Members", len(data_manager.get_all_members()))

        with col2:
            st.metric("Total Donations", f"{stats['total_donations']:,.0f} gil")
            st.metric("Total Expenses", f"{stats['total_expenses']:,.0f} gil")

        # Show recent activity
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Recent Donations")
            donations = data_manager.get_donations()
            if not donations.empty:
                for idx, donation in donations.head(5).iterrows():
                    member_summary = data_manager.get_member_donation_summary(donation['member_name'])
                    with st.expander(f"{donation['member_name']} - {donation['amount']:,.0f} gil"):
                        st.write(f"Total Lifetime Donations: {member_summary['total_amount']:,.0f} gil")
                        st.write(f"Number of Donations: {member_summary['donation_count']}")
                        st.write(f"First Donation: {member_summary['first_donation']}")
                        st.write(f"Latest Donation: {member_summary['last_donation']}")
                        if pd.notna(donation['notes']) and donation['notes']:
                            st.write(f"Notes: {donation['notes']}")
            else:
                st.info("No recent donations")

        with col2:
            st.subheader("Recent Expenses")
            expenses = data_manager.get_expenses_list()
            if not expenses.empty:
                for _, expense in expenses.sort_values('date', ascending=False).head(5).iterrows():
                    with st.expander(f"{expense['category']} - {expense['amount']:,.0f} gil"):
                        st.write(f"Description: {expense['description']}")
                        st.write(f"Category: {expense['category']}")
                        st.write(f"Approved by: {expense['approved_by']}")
                        st.write(f"Date: {expense['date']}")
            else:
                st.info("No recent expenses")

    # Donations
    elif page == "Donations":
        st.subheader("FC Donations")

        with st.expander("➕ Add New Donation"):
            members = data_manager.get_all_members()
            donor = st.selectbox("Select Member", members['name'].tolist(), key="donor_select_new_donation")
            amount = st.number_input("Donation Amount (gil)", min_value=0, value=0, key="amount_input_new_donation")
            notes = st.text_area("Notes", key="notes_input_new_donation")

            if st.button("Record Donation", key="submit_new_donation"):
                if donor and amount > 0:
                    if data_manager.add_donation(donor, amount, notes):
                        st.success("Donation recorded successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to record donation")
                else:
                    st.error("Please fill in all required fields")

        # Show donation history
        donations = data_manager.get_donations()
        if not donations.empty:
            st.subheader("Donation History")

            # Get unique members and their donation summaries
            unique_members = donations['member_name'].unique()
            member_totals = []
            for member in unique_members:
                summary = data_manager.get_member_donation_summary(member)
                if summary:
                    member_totals.append({
                        'member_name': member,
                        'total_amount': summary['total_amount'],
                        'summary': summary
                    })

            # Sort members by total donation amount (highest to lowest)
            member_totals.sort(key=lambda x: x['total_amount'], reverse=True)

            # Display sorted donations
            for member_data in member_totals:
                member = member_data['member_name']
                summary = member_data['summary']

                with st.expander(f"{member} - Total: {summary['total_amount']:,.0f} gil ({summary['donation_count']} donations)"):
                    st.write(f"First Donation: {summary['first_donation']}")
                    st.write(f"Last Donation: {summary['last_donation']}")

                    # Shared notes for all member's donations
                    sample_donation = summary['donations'][0]
                    new_notes = st.text_area(
                        "Notes (applies to all donations)",
                        value=sample_donation['notes'] if pd.notna(sample_donation['notes']) else "",
                        key=f"notes_{member}"
                    )

                    if st.button("Update Notes", key=f"update_{member}"):
                        if data_manager.update_member_donations_notes(member, new_notes):
                            st.success("Notes updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update notes")

                    st.write("---")
                    st.write("Donation History:")

                    # Show individual donations without individual notes
                    for donation in summary['donations']:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"Amount: {donation['amount']:,.0f} gil - Date: {donation['date']}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_{donation['timestamp']}", type="secondary"):
                                if data_manager.delete_donation(donation['timestamp']):
                                    st.success("Donation deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete donation")
        else:
            st.info("No donations recorded yet")

    # Housing Bids
    elif page == "Housing Bids":
        st.subheader("Housing Lotto Numbers")

        with st.expander("➕ Record New Lotto Number"):
            members = data_manager.get_all_members()
            bid_member = st.selectbox("Select Member", members['name'].tolist(), key="bid_member")
            bid_number = st.number_input("Lotto Number", min_value=1, value=1)

            if st.button("Record Lotto Number"):
                if bid_member and bid_number:
                    data_manager.add_bid(bid_member, bid_number)
                    st.success("Lotto number recorded successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")

        bids = pd.read_csv("data/bids.csv")
        if not bids.empty:
            st.subheader("All Lotto Numbers")
            for _, bid in bids.sort_values(['date', 'bid_number'], ascending=[False, True]).iterrows():
                with st.expander(f"Lotto #{bid['bid_number']} - {bid['member_name']}"):
                    st.write(f"Date: {bid['date']}")

                    # Edit lotto number
                    new_number = st.number_input("Edit Lotto Number",
                                                min_value=1,
                                                value=int(bid['bid_number']),
                                                key=f"edit_{bid['date']}_{bid['bid_number']}"
                                                )
                    if st.button("Update Number", key=f"update_{bid['date']}_{bid['bid_number']}"):
                        data_manager.update_bid_number(bid['member_name'], bid['bid_number'], bid['date'], new_number)
                        st.success("Lotto number updated successfully!")
                        st.rerun()

                    # Delete lotto number
                    if st.button("🗑️ Delete Lotto Number",
                                key=f"delete_{bid['date']}_{bid['bid_number']}",
                                type="secondary"
                                ):
                        data_manager.delete_bid(bid['member_name'], bid['bid_number'], bid['date'])
                        st.success("Lotto number deleted successfully!")
                        st.rerun()
        else:
            st.info("No lotto numbers recorded")

    # Expenses
    elif page == "Expenses":
        st.subheader("FC Expenses")

        with st.expander("➕ Record New Expense"):
            amount = st.number_input("Expense Amount (gil)", min_value=0, value=0)
            category = st.selectbox(
                "Category",
                options=data_manager.expense_categories,
                help="Select the type of expense"
            )
            description = st.text_area("Description")
            approved_by = st.selectbox("Approved By", data_manager.get_all_members()['name'].tolist())

            if st.button("Record Expense"):
                if amount > 0 and description and approved_by:
                    data_manager.add_expense(amount, description, category, approved_by)
                    st.success("Expense recorded successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")

        # Show expense statistics
        st.subheader("Expense Statistics")
        category_totals = data_manager.get_expenses_by_category()

        cols = st.columns(len(data_manager.expense_categories))
        for i, category in enumerate(data_manager.expense_categories):
            with cols[i]:
                st.metric(category, f"{category_totals[category]:,.0f} gil")

        # Show expense history
        st.subheader("Expense History")
        selected_category = st.selectbox(
            "Filter by Category",
            ["All Categories"] + data_manager.expense_categories
        )

        expenses = data_manager.get_expenses_list()
        if not expenses.empty:
            if selected_category != "All Categories":
                expenses = expenses[expenses['category'] == selected_category]

            for _, expense in expenses.sort_values('date', ascending=False).iterrows():
                with st.expander(f"{expense['date']} - {expense['category']} - {expense['amount']:,.0f} gil"):
                    st.write(f"Amount: {expense['amount']:,.0f} gil")
                    st.write(f"Category: {expense['category']}")
                    st.write(f"Approved by: {expense['approved_by']}")

                    # Edit description
                    new_description = st.text_area("Edit Description", value=expense['description'], key=f"desc_{expense['date']}_{expense['amount']}")
                    if st.button("Update Description", key=f"update_{expense['date']}_{expense['amount']}"):
                        data_manager.update_expense_notes(expense['date'], expense['amount'], expense['description'], new_description)
                        st.success("Description updated successfully!")
                        st.rerun()

                    # Delete expense
                    if st.button("🗑️ Delete Expense", key=f"delete_{expense['date']}_{expense['amount']}", type="secondary"):
                        data_manager.delete_expense(expense['date'], expense['amount'], expense['description'])
                        st.success("Expense deleted successfully!")
                        st.rerun()
        else:
            st.info("No expenses recorded yet")

    # Members List
    elif page == "Members List":
        st.subheader("FC Members")

        col1, col2 = st.columns([2, 3])

        with col1:
            if st.button("🔄 Sync Members from Lodestone"):
                with st.spinner("Syncing members from Lodestone..."):
                    members_count = data_manager.sync_members_from_lodestone()
                    if members_count > 0:
                        st.success(f"Updated member list with {members_count} members from Lodestone!")
                    else:
                        st.error("Failed to sync members from Lodestone")
                st.rerun()

            search_term = st.text_input("🔍 Search Members")

            members = data_manager.get_all_members()
            if search_term:
                filtered_members = members[members['name'].str.contains(search_term, case=False, na=False)]
            else:
                filtered_members = members

            if not filtered_members.empty:
                selected_member = st.selectbox(
                    "Select a member to view details",
                    filtered_members['name'].tolist(),
                    key="member_selector"
                )
            else:
                st.info("No members found matching your search.")
                selected_member = None

        with col2:
            if selected_member:
                st.subheader(f"Member Details: {selected_member}")

                # Show member's bids
                member_bids = data_manager.get_member_bids(selected_member)
                if not member_bids.empty:
                    st.write("Housing Bids:")
                    for _, bid in member_bids.iterrows():
                        with st.expander(f"Housing Bid #{bid['bid_number']}"):
                            st.write(f"Date: {bid['date']}")

                # Show donations
                member_donations = data_manager.get_member_donations(selected_member)
                st.subheader("Donations")
                if not member_donations.empty:
                    total_donations = member_donations['amount'].sum()
                    st.metric("Total Donations", f"{total_donations:,.0f} gil")
                    for _, donation in member_donations.iterrows():
                        st.write(f"Amount: {donation['amount']:,.0f} gil - Date: {donation['date']}")
                else:
                    st.info("No donations recorded")

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center'>Lotus Free Company</p>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error initializing application: {str(e)}")
    st.info("If this error persists, please contact support.")