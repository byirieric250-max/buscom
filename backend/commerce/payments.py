import base64
import json
import os
import uuid
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

def _post_json(url,payload,headers,timeout=15):
 if not url: raise RuntimeError('Provider URL is not configured.')
 req=urllib_request.Request(url,data=json.dumps(payload).encode(),headers={**headers,'Content-Type':'application/json'},method='POST')
 try:
  with urllib_request.urlopen(req,timeout=timeout) as response:
   body=response.read().decode()
   return json.loads(body) if body else {}
 except (HTTPError,URLError,TimeoutError) as exc:
  raise RuntimeError('The Mobile Money provider is temporarily unavailable.') from exc

def request_collection(payment,phone):
 provider=payment.provider
 if provider=='mtn_momo':
  api_url=os.getenv('MTN_MOMO_COLLECTION_URL','https://proxy.momoapi.mtn.com/collection/v1_0/requesttopay').strip()
  token_url=os.getenv('MTN_MOMO_TOKEN_URL','https://proxy.momoapi.mtn.com/collection/token').strip()
  api_key=os.getenv('MTN_MOMO_API_KEY','').strip(); api_user=os.getenv('MTN_MOMO_API_USER','').strip(); subscription_key=os.getenv('MTN_MOMO_SUBSCRIPTION_KEY','').strip()
  if not all((api_key,api_user,subscription_key)): raise RuntimeError('MTN Mobile Money credentials are not configured.')
  auth=base64.b64encode(f'{api_user}:{api_key}'.encode()).decode()
  token=_post_json(token_url,None,{'Authorization':f'Basic {auth}','Ocp-Apim-Subscription-Key':subscription_key})
  access_token=token.get('access_token')
  if not access_token: raise RuntimeError('MTN Mobile Money authentication failed.')
  reference=str(uuid.uuid4()); payment.provider_reference=reference
  _post_json(api_url,{
   'amount':str(payment.amount),'currency':'RWF','externalId':payment.order.reference,
   'payer':{'partyIdType':'MSISDN','partyId':phone},
   'payerMessage':f'Escrow payment for {payment.order.reference}','payeeNote':'Temporary escrow hold'
  },{'Authorization':f'Bearer {access_token}','X-Reference-Id':reference,'X-Target-Environment':os.getenv('MTN_MOMO_ENVIRONMENT','sandbox'),'Ocp-Apim-Subscription-Key':subscription_key})
  return reference
 if provider=='airtel_money':
  api_url=os.getenv('AIRTEL_MONEY_COLLECTION_URL','').strip()
  token_url=os.getenv('AIRTEL_MONEY_TOKEN_URL','').strip()
  client_id=os.getenv('AIRTEL_MONEY_CLIENT_ID','').strip(); client_secret=os.getenv('AIRTEL_MONEY_CLIENT_SECRET','').strip()
  if not all((api_url,token_url,client_id,client_secret)): raise RuntimeError('Airtel Money credentials are not configured.')
  token=_post_json(token_url,{'client_id':client_id,'client_secret':client_secret,'grant_type':'client_credentials'},{})
  access_token=token.get('access_token') or token.get('token')
  if not access_token: raise RuntimeError('Airtel Money authentication failed.')
  reference=str(uuid.uuid4()); payment.provider_reference=reference
  result=_post_json(api_url,{
   'reference':reference,'transaction':{'amount':str(payment.amount),'country':'RW','currency':'RWF','id':payment.order.reference},
   'subscriber':{'country':'RW','currency':'RWF','msisdn':phone}
  },{'Authorization':f'Bearer {access_token}'})
  return result.get('transaction',{}).get('id',reference)
 raise RuntimeError('Unsupported Mobile Money provider.')

def transfer_to_seller(payment,business,amount):
 provider=payment.provider
 if provider=='mtn_momo':
  transfer_url=os.getenv('MTN_MOMO_DISBURSEMENT_URL','https://proxy.momoapi.mtn.com/disbursement/v1_0/transfer').strip()
  token_url=os.getenv('MTN_MOMO_TRANSFER_TOKEN_URL','https://proxy.momoapi.mtn.com/disbursement/token').strip()
  api_key=os.getenv('MTN_MOMO_TRANSFER_API_KEY',os.getenv('MTN_MOMO_API_KEY','')).strip()
  api_user=os.getenv('MTN_MOMO_TRANSFER_API_USER',os.getenv('MTN_MOMO_API_USER','')).strip()
  subscription_key=os.getenv('MTN_MOMO_TRANSFER_SUBSCRIPTION_KEY',os.getenv('MTN_MOMO_SUBSCRIPTION_KEY','')).strip()
  if not all((api_key,api_user,subscription_key)): raise RuntimeError('MTN disbursement credentials are not configured.')
  auth=base64.b64encode(f'{api_user}:{api_key}'.encode()).decode()
  token=_post_json(token_url,None,{'Authorization':f'Basic {auth}','Ocp-Apim-Subscription-Key':subscription_key})
  access_token=token.get('access_token'); reference=str(uuid.uuid4())
  if not access_token: raise RuntimeError('MTN disbursement authentication failed.')
  _post_json(transfer_url,{
   'amount':str(amount),'currency':'RWF','externalId':payment.order.reference,
   'payee':{'partyIdType':'MSISDN','partyId':business.phone},
   'payerMessage':f'Settlement for {payment.order.reference}','payeeNote':'Buyer-confirmed marketplace receipt'
  },{'Authorization':f'Bearer {access_token}','X-Reference-Id':reference,'X-Target-Environment':os.getenv('MTN_MOMO_ENVIRONMENT','sandbox'),'Ocp-Apim-Subscription-Key':subscription_key})
  return reference
 if provider=='airtel_money':
  transfer_url=os.getenv('AIRTEL_MONEY_DISBURSEMENT_URL','').strip()
  token_url=os.getenv('AIRTEL_MONEY_TOKEN_URL','').strip()
  client_id=os.getenv('AIRTEL_MONEY_CLIENT_ID','').strip(); client_secret=os.getenv('AIRTEL_MONEY_CLIENT_SECRET','').strip()
  if not all((transfer_url,token_url,client_id,client_secret)): raise RuntimeError('Airtel disbursement credentials are not configured.')
  token=_post_json(token_url,{'client_id':client_id,'client_secret':client_secret,'grant_type':'client_credentials'},{})
  access_token=token.get('access_token') or token.get('token'); reference=str(uuid.uuid4())
  if not access_token: raise RuntimeError('Airtel disbursement authentication failed.')
  _post_json(transfer_url,{
   'reference':reference,'transaction':{'amount':str(amount),'country':'RW','currency':'RWF','id':payment.order.reference},
   'payee':{'country':'RW','currency':'RWF','msisdn':business.phone}
  },{'Authorization':f'Bearer {access_token}'})
  return reference
 raise RuntimeError('Unsupported payout provider.')
