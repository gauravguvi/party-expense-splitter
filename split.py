import streamlit as st

st.set_page_config(page_title="Party Expense Splitter", page_icon="💰")

st.title("💰 Party Expense Splitter")
st.write("Add people, expenses and select who shares each expense.")

# -------------------------
# PEOPLE
# -------------------------

st.header("1. Add People")

num_people = st.number_input("Number of people", min_value=1, max_value=50, value=3, step=1)

names = []
for i in range(int(num_people)):
    name = st.text_input(
        f"Person {i + 1}",
        value=["Gaurav", "Prince", "Chetan"][i] if i < 3 else "",
        key=f"name_{i}"
    ).strip()
    names.append(name)

valid_names = [n for n in names if n]
names_valid = len(valid_names) == len(names) and len(set(n.lower() for n in names)) == len(names)

# Clear expenses if names change
if "last_names" not in st.session_state:
    st.session_state.last_names = names[:]

if st.session_state.last_names != names:
    st.session_state.expenses = []
    st.session_state.last_names = names[:]

# -------------------------
# EXPENSES
# -------------------------

if "expenses" not in st.session_state:
    st.session_state.expenses = []

st.header("2. Add Expenses")

if names_valid:
    with st.form("expense_form", clear_on_submit=True):
        payer = st.selectbox("Who paid?", names)
        amount = st.number_input("Expense amount (₹)", min_value=0.01, value=100.0, step=100.0)
        participants = st.multiselect("Split this expense among:", names, default=names)
        submitted = st.form_submit_button("Add Expense")

        if submitted:
            if not participants:
                st.error("Select at least one participant.")
            else:
                st.session_state.expenses.append({
                    "payer": payer,
                    "amount": round(amount, 2),
                    "participants": participants.copy()
                })
                st.success("Expense added!")
else:
    st.warning("Please enter unique names for all people.")

# -------------------------
# DISPLAY EXPENSES
# -------------------------

st.header("3. Expense List")

if st.session_state.expenses:
    for i, expense in enumerate(st.session_state.expenses):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{expense['payer']}** paid ₹{expense['amount']:.2f}")
            st.caption("Shared by: " + ", ".join(expense["participants"]))
        with col2:
            if st.button("Delete", key=f"delete_{i}"):
                st.session_state.expenses.pop(i)
                st.rerun()

    if st.button("Clear All Expenses"):
        st.session_state.expenses = []
        st.rerun()
else:
    st.info("No expenses added yet.")

# -------------------------
# CALCULATE SPLIT
# -------------------------

st.header("4. Calculate Final Split")

if st.button("Calculate Settlement", type="primary"):
    if not st.session_state.expenses:
        st.error("Please add at least one expense.")
    elif not names_valid:
        st.error("Please enter unique names for everyone.")
    else:
        paid = {name: 0 for name in names}
        share = {name: 0 for name in names}

        for expense in st.session_state.expenses:
            amt = round(expense["amount"] * 100)
            participants = expense["participants"]
            paid[expense["payer"]] += amt
            base = amt // len(participants)
            remainder = amt % len(participants)
            for idx, person in enumerate(participants):
                share[person] += base + (1 if idx < remainder else 0)

        balance = {person: paid[person] - share[person] for person in names}

        st.header("5. Final Summary")
        st.metric("Total Party Expense", f"₹{sum(paid.values()) / 100:.2f}")

        st.subheader("Person-wise Split")
        summary = []
        for person in names:
            net = balance[person]
            settlement = f"Receives ₹{net / 100:.2f}" if net > 0 else (f"Pays ₹{-net / 100:.2f}" if net < 0 else "Settled")
            summary.append({
                "Person": person,
                "Amount Paid": f"₹{paid[person] / 100:.2f}",
                "Share": f"₹{share[person] / 100:.2f}",
                "Settlement": settlement
            })
        st.dataframe(summary, use_container_width=True, hide_index=True)

        # -------------------------
        # PAYMENT SETTLEMENT
        # -------------------------

        st.subheader("6. Who Pays Whom?")

        debtors = [[p, -v] for p, v in balance.items() if v < 0]
        creditors = [[p, v] for p, v in balance.items() if v > 0]
        transactions = []
        i, j = 0, 0

        while i < len(debtors) and j < len(creditors):
            amt = min(debtors[i][1], creditors[j][1])
            transactions.append({"From": debtors[i][0], "To": creditors[j][0], "Amount": f"₹{amt / 100:.2f}"})
            debtors[i][1] -= amt
            creditors[j][1] -= amt
            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        if transactions:
            st.dataframe(transactions, use_container_width=True, hide_index=True)
        else:
            st.success("Everyone is settled!")

        st.success("Expense split calculated successfully!")
