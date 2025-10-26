from hedera import Client, AccountId, PrivateKey, Hbar, AccountBalanceQuery
from api.utils.settings import settings

account_id = AccountId.fromString(settings.HEDERA_OPERATOR_ID)
private_key = PrivateKey.fromString(settings.HEDERA_OPERATOR_KEY)

client = Client.forTestnet()
client.setOperator(account_id, private_key)

account_balance = AccountBalanceQuery().setAccountId(account_id).execute(client)
print(f"Your account balance is: {account_balance.hbars.toTinybars()} tinybars")