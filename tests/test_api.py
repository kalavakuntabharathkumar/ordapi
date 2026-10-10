from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_health():
    assert client.get('/health').json()=={'status':'ok'}

def test_product_crud_and_duplicate_sku():
    sku='TEST-API-1001'
    r=client.post('/products',json={'sku':sku,'name':'Test Widget','price':12.5,'quantity':10})
    assert r.status_code==201, r.text
    pid=r.json()['id']
    assert client.get(f'/products/{pid}').json()['sku']==sku
    assert client.post('/products',json={'sku':sku,'name':'Dup','price':1,'quantity':1}).status_code==409
    assert client.patch(f'/products/{pid}',json={'quantity':8}).json()['quantity']==8
    assert client.delete(f'/products/{pid}').status_code==204

def test_order_reserves_stock():
    r=client.post('/products',json={'sku':'TEST-ORDER-1002','name':'Order Item','price':7,'quantity':5})
    pid=r.json()['id']
    order=client.post('/orders',json={'customer_name':'Demo Customer','items':[{'product_id':pid,'quantity':2}]})
    assert order.status_code==201, order.text
    assert order.json()['total']==14
    assert client.get(f'/products/{pid}').json()['quantity']==3
    assert client.post('/orders',json={'customer_name':'No Stock','items':[{'product_id':pid,'quantity':99}]}).status_code==409
