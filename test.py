import pyupbit

access = "EKJFovcB2RDrRkfmUos8I6USo8QYx8t56LjFqAQt"          # 본인 값으로 변경
secret = "nTOdgh3bzQEtPiUaKJpazEKFSEeU1etYdIFcbsV5"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-BTC"))     # KRW-XRP 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회
