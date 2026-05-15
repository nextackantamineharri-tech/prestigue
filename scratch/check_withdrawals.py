from app import create_app, db
from app.models.finance import Withdrawal
from app.models.user import User

app = create_app()
with app.app_context():
    withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).limit(10).all()
    print(f"{'ID':<5} | {'User':<20} | {'Amount':<10} | {'Status':<10} | {'Address':<20}")
    print("-" * 75)
    for w in withdrawals:
        user = User.query.get(w.user_id)
        print(f"{w.id:<5} | {user.email:<20} | {w.amount:<10} | {w.status:<10} | {w.wallet_address:<20}")
