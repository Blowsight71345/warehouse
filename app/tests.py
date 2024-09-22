import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import get_db, Base
from environs import Env

env = Env()
env.read_env()
#для работы с postgres
POSTGRES_DB = env("TEST_POSTGRES_DB")
POSTGRES_USER = env("POSTGRES_USER")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD")
POSTGRES_HOST = env("POSTGRES_HOST")
POSTGRES_PORT = env("POSTGRES_PORT")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
#для работы с sqlite
# DATABASE_URL = "sqlite:///./app.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# тестовая бд для sqlite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    with TestClient(app) as c:
        yield c


def test_create_product(client):
    response = client.post("/products/", json={"name": "Test Product", "price": 10.0, "stock": 100})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"


def test_create_product_invalid_price(client):
    response = client.post("/products/", json={"name": "Test Product", "price": -10.0, "stock": 100})
    assert response.status_code == 422


def test_read_products(client):
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_product(client):
    response = client.post("/products/", json={"name": "Another Product", "price": 15.0, "stock": 50})
    product_id = response.json()["id"]
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


def test_update_product(client):
    response = client.post("/products/", json={"name": "Update Product", "price": 12.0, "stock": 20})
    product_id = response.json()["id"]
    response = client.put(f"/products/{product_id}", json={"name": "Updated Product", "price": 15.0, "stock": 30})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Product"


#
def test_delete_product(client):
    response = client.post("/products/", json={"name": "Delete Product", "price": 20.0, "stock": 5})
    product_id = response.json()["id"]
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Product deleted"


def test_create_order(client):
    response = client.post("/products/", json={"name": "Order Product", "price": 10.0, "stock": 10})
    product_id = response.json()["id"]
    order_data = {
        "created_at": "2022-01-01 00:00:00",
        "status": "доставлен",
        "items": [
            {"product_id": product_id, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200
    assert response.json()["status"] == "доставлен"


def test_read_orders(client):
    response = client.get("/orders/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_order(client):
    response = client.post("/products/", json={"name": "Order Product", "price": 10.0, "stock": 10})
    product_id = response.json()["id"]

    order_data = {
        "created_at": "2022-01-01 00:00:00",
        "status": "отправлен",
        "items": [
            {"product_id": product_id, "quantity": 1}
        ]
    }
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["id"]

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_update_order_status(client):
    response = client.post("/products/", json={"name": "Update Order Product", "price": 10.0, "stock": 10})
    product_id = response.json()["id"]

    order_data = {
        "created_at": "2022-01-01 00:00:00",
        "status": "в процессе",
        "items": [
            {"product_id": product_id, "quantity": 1}
        ]
    }
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["id"]

    update_data = {"status": "отправлен"}
    response = client.patch(f"/orders/{order_id}/status", json=update_data)
    assert response.status_code == 200
    assert response.json()["status"] == "отправлен"


@pytest.mark.parametrize("invalid_status", ["INVALID", "NOTEXISTING"])
def test_update_order_invalid_status(client, invalid_status):
    response = client.post("/products/", json={"name": "Test Product", "price": 10.0, "stock": 10})
    product_id = response.json()["id"]

    order_data = {
        "created_at": "2022-01-01 00:00:00",
        "status": "в процессе",
        "items": [
            {"product_id": product_id, "quantity": 1}
        ]
    }
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["id"]

    update_data = {"status": invalid_status}
    response = client.patch(f"/orders/{order_id}/status", json=update_data)
    assert response.status_code == 422
