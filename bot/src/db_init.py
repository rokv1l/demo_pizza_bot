import json

from .database import session_maker, Product


with open("src/products_data/data.json", "r") as f:
    data = json.load(f)
    with session_maker() as session:
        for name in data:
            is_exists = session.query(Product).filter(Product.name == name).exists()
            if not is_exists:
                continue
            product = Product(
                name=name,
                image=f"src/products_data/images/{data[name]['image']}",
                description=data[name]["description"],
                cost=data[name]["cost"]
            )
            session.add(product)
            session.commit()
