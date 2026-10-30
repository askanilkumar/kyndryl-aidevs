"""NetNova Telecom sample data (all fictional)."""

CUSTOMERS = {
    "C-101": {"name": "Ravi Kumar", "plan": "Postpaid Platinum 999", "phone": "9876543210",
              "email": "ravi.kumar@example.com", "sim": "active"},
    "C-102": {"name": "Meera Iyer", "plan": "Prepaid Smart 299", "phone": "9123456780",
              "email": "meera.iyer@example.com", "sim": "active"},
    "C-103": {"name": "Arjun Rao", "plan": "Postpaid Gold 599", "phone": "9988776655",
              "email": "arjun.rao@example.com", "sim": "blocked"},
}

TICKETS = {
    "INC-5001": {"customer": "C-101", "status": "open", "issue": "Slow 5G data in Chennai T. Nagar since Monday",
                 "note": "Tower CHN-07 under maintenance, ETA 2 days"},
    "INC-5002": {"customer": "C-102", "status": "open", "issue": "Recharge of Rs 299 not reflected",
                 "note": "Payment gateway delay, auto-credit within 24 hours"},
    "INC-5003": {"customer": "C-103", "status": "resolved", "issue": "SIM blocked after 3 wrong PUK tries",
                 "note": "New SIM issued at store"},
}

KB = [
    {"id": "KB-01", "title": "Slow mobile data", "audience": "public",
     "text": "Restart the phone, check data balance, switch to 4G/5G auto mode. If slow for more than 24 hours, raise a ticket."},
    {"id": "KB-02", "title": "Roaming prices", "audience": "public",
     "text": "International roaming: prepaid Rs 649 per day, postpaid Rs 499 per day in UAE, Singapore and Thailand."},
    {"id": "KB-03", "title": "SIM reset", "audience": "public",
     "text": "A SIM reset re-registers the SIM on the network. It needs supervisor approval and takes about 10 minutes."},
    {"id": "KB-04", "title": "Bill payment", "audience": "public",
     "text": "Pay bills on the NetNova app or website. Late fee is Rs 100 after the due date."},
    {"id": "KB-05", "title": "Plan change", "audience": "public",
     "text": "Postpaid plans can be changed once per billing cycle. The new plan starts from the next cycle."},
    {"id": "KB-90", "title": "INTERNAL NOC escalation runbook", "audience": "internal",
     "text": "INTERNAL ONLY. Escalate P1 outages to the NOC bridge ESC-901 and call the duty manager."},
]
