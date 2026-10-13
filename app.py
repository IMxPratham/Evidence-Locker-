import json, hashlib, datetime
import streamlit as st
from web3 import Web3

st.set_page_config(page_title="Evidence Locker", layout="wide")

# ---------- connect (cached so it runs once) ----------
@st.cache_resource
def connect():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    info = json.load(open("deployment.json"))   # {"address": "...", "abi": [...]}
    return w3, w3.eth.contract(address=info["address"], abi=info["abi"])

w3, locker = connect()
accounts = w3.eth.accounts
roles = {"Owner": accounts[0], "Investigator 1": accounts[1], "Investigator 2": accounts[2]}
name_of = {v: k for k, v in roles.items()}

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()          # 32 bytes = bytes32

def send(fn, sender):
    """Send a transaction from `sender` and wait until it is mined."""
    tx = fn.transact({"from": sender})
    return w3.eth.wait_for_transaction_receipt(tx)

# ---------- sidebar ----------
st.sidebar.header("Acting as")
role = st.sidebar.selectbox("Account", list(roles))
me = roles[role]
st.sidebar.code(me)
is_owner = role == "Owner"
st.title("Blockchain Evidence Locker")

tab_reg, tab_ver, tab_tr, tab_hist = st.tabs(["Register", "Verify", "Transfer", "History"])

# ---------- Register ----------
with tab_reg:
    if not is_owner:
        st.info("Only the Owner registers evidence in this version.")
    f = st.file_uploader("Evidence file", key="reg")
    case = st.text_input("Case ID", "CASE-001")
    desc = st.text_input("Description")
    if st.button("Register", disabled=not (is_owner and f)):
        try:
            h = sha256_bytes(f.getvalue())
            send(locker.functions.registerEvidence(h, case, desc), me)
            st.success(f"Registered as ID {locker.functions.evidenceCount().call()}")
            st.code("0x" + h.hex())
        except Exception as e:
            st.error(str(e))

# ---------- Verify ----------
with tab_ver:
    vid = st.number_input("Evidence ID", min_value=1, step=1, key="vid")
    vf = st.file_uploader("File to check", key="ver")
    if st.button("Verify", disabled=not vf):
        try:
            ok = locker.functions.verifyEvidence(int(vid), sha256_bytes(vf.getvalue())).call()
            (st.success if ok else st.error)(
                "VALID: file matches the blockchain record" if ok
                else "TAMPERED: file does NOT match")
        except Exception as e:
            st.error(str(e))

# ---------- Transfer ----------
with tab_tr:
    tid = st.number_input("Evidence ID", min_value=1, step=1, key="tid")
    to_name = st.selectbox("Transfer to", [n for n in roles if roles[n] != me])
    tf = st.file_uploader("Re-upload file to verify before handover", key="tr")
    verified = False
    if tf:
        try:
            verified = locker.functions.verifyEvidence(int(tid), sha256_bytes(tf.getvalue())).call()
            (st.success if verified else st.error)("VALID" if verified else "TAMPERED: transfer blocked")
        except Exception as e:
            st.error(str(e))
    if st.button("Transfer custody", disabled=not verified):
        try:
            send(locker.functions.transferCustody(int(tid), roles[to_name]), me)
            st.success(f"Custody moved to {to_name}")
        except Exception as e:
            st.error(str(e))

# ---------- History ----------
with tab_hist:
    hid = st.number_input("Evidence ID", min_value=1, step=1, key="hid")
    if st.button("Show history"):
        rows = []
        for ev in locker.events.EvidenceRegistered().get_logs(from_block=0, argument_filters={"id": int(hid)}):
            a = ev["args"]
            rows.append((ev["blockNumber"], "REGISTERED", name_of.get(a["by"], a["by"]), "", a["caseId"]))
        for ev in locker.events.CustodyTransferred().get_logs(from_block=0, argument_filters={"id": int(hid)}):
            a = ev["args"]
            rows.append((ev["blockNumber"], "TRANSFERRED", name_of.get(a["from"], a["from"]), name_of.get(a["to"], a["to"]), ""))
        rows.sort()
        st.dataframe(
            [{"Block": r[0], "Action": r[1], "From/By": r[2], "To": r[3], "Case": r[4]} for r in rows],
            use_container_width=True)