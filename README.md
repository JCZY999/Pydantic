# Pydantic Tutorials

A practical introduction to **Pydantic v2** for validating, transforming, and serializing Python data. Each tutorial is self-contained and can be copied into a Python file and run.

## Worked case study

[Open the executed Pydantic case-study notebook](pydantic-advanced-case-study.ipynb).

Follow eight synthetic lead records from messy input through validation, error reporting, serialization and a final intake decision. Includes a chart, assertions, strict versus permissive validation, nested models, validators, tagged unions and function validation. No API keys or external services are needed.

```bash
python -m pip install -r requirements.txt
python case_study.py
python -m pytest -q
python execute_notebook.py
```

Reusable code: [`case_study.py`](case_study.py). Tests: [`tests/test_case_study.py`](tests/test_case_study.py). The original introductory tutorials remain below.

## Setup

Use Python 3.11 or newer and install Pydantic:

```bash
python -m pip install "pydantic>=2,<3"
```

Pydantic uses Python type hints at runtime. Valid input becomes a predictable model; invalid input raises a clear `ValidationError`.

## Tutorial 1: Your first model

Use `BaseModel` at application boundaries—for example, when accepting an API request or reading a job configuration.

```python
from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str
    active: bool = True


user = User.model_validate({"id": "42", "name": "Ada"})
print(user)
print(type(user.id))  # <class 'int'>

try:
    User.model_validate({"id": "not-a-number", "name": "Ada"})
except ValidationError as error:
    print(error)
```

By default, Pydantic can coerce compatible values. Here, `"42"` becomes `42`. Use strict types or strict configuration when coercion is undesirable.

## Tutorial 2: Add constraints with Field

`Field` attaches validation rules and metadata to fields. This is useful for enforcing business rules close to the schema.

```python
from typing import Annotated

from pydantic import BaseModel, Field

PositivePrice = Annotated[float, Field(gt=0)]


class Product(BaseModel):
    sku: str = Field(min_length=3, max_length=20)
    price: PositivePrice
    quantity: int = Field(ge=0, default=0)


product = Product(sku="BOOK-01", price=12.50, quantity=3)
print(product.model_dump())
```

The model rejects empty SKUs, non-positive prices, and negative quantities before bad data reaches the rest of your program.

## Tutorial 3: Custom field and model validators

Use a field validator for one field and a model validator for rules involving multiple fields.

```python
from typing import Self

from pydantic import BaseModel, field_validator, model_validator


class Registration(BaseModel):
    username: str
    password: str
    password_repeat: str

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().lower()
        if " " in value:
            raise ValueError("username cannot contain spaces")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("passwords do not match")
        return self


registration = Registration(
    username="  GraceHopper  ",
    password="correct-horse",
    password_repeat="correct-horse",
)
print(registration.username)
```

Validators should perform focused domain checks. Keep unrelated I/O and database work outside the model.

## Tutorial 4: Nested models

Large payloads become easier to understand when each concept has its own model.

```python
from pydantic import BaseModel


class Address(BaseModel):
    city: str
    country: str


class Customer(BaseModel):
    name: str
    address: Address
    tags: list[str] = []


customer = Customer.model_validate(
    {
        "name": "Lin",
        "address": {"city": "Phoenix", "country": "US"},
        "tags": ["beta", "newsletter"],
    }
)
print(customer.address.city)
```

Pydantic recursively converts the address dictionary into an `Address` instance and validates the list elements.

## Tutorial 5: Serialize models and generate schemas

Use `model_dump()` for Python data, `model_dump_json()` for JSON, and `model_json_schema()` for tooling or API documentation.

```python
from datetime import datetime, timezone

from pydantic import BaseModel


class Event(BaseModel):
    name: str
    occurred_at: datetime


event = Event(name="model-trained", occurred_at=datetime.now(timezone.utc))
print(event.model_dump())
print(event.model_dump_json(indent=2))
print(Event.model_json_schema())
```

Serialization is especially useful when passing validated data to message queues, APIs, logs, or storage layers.

## Tutorial 6: Validate non-model types with TypeAdapter

`TypeAdapter` applies Pydantic validation to lists, dictionaries, unions, and other type annotations without creating a `BaseModel`.

```python
from pydantic import TypeAdapter

integer_list = TypeAdapter(list[int])
values = integer_list.validate_python(["1", 2, 3.0])
print(values)  # [1, 2, 3]
print(integer_list.dump_json(values))
```

This is handy for validating a single function input, file fragment, or collection.

## Tutorial 7: Validate function calls

The `validate_call` decorator validates arguments using their annotations before the function runs.

```python
from pydantic import Field, validate_call
from typing import Annotated


@validate_call
def repeat_message(message: str, count: Annotated[int, Field(gt=0)]) -> list[str]:
    return [message] * count


print(repeat_message("ready", "3"))
```

Use this at carefully chosen boundaries. It adds runtime work, so ordinary internal functions can usually rely on static type checking instead.

## Practice ideas

1. Add an email field using `EmailStr` and install `pydantic[email]`.
2. Make a model strict with `ConfigDict(strict=True)` and compare its behavior.
3. Add aliases for incoming camelCase JSON.
4. Write tests for both valid and invalid payloads.
5. Build a nested configuration model for an ML training job.

## Key takeaways

- Type hints describe the desired output shape; Pydantic validates input against it.
- Put models at system boundaries where untrusted or loosely typed data enters.
- Prefer small nested models over one enormous schema.
- Catch `ValidationError` where you can turn it into a useful response.
- Use Pydantic v2 methods such as `model_validate`, `model_dump`, and `model_dump_json`.

## References

- [Pydantic documentation](https://docs.pydantic.dev/)
- [Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
